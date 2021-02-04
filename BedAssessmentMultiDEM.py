# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.2 - Nov 2020 - Création, à partir de BedAssessment.py v1.1



import os
import arcpy
import pickle
from RasterIO import *
from tree.OurTreeSegment import *
from tree.OurTreeManager import *
#from Solver2 import *
from SolverLisflood import *
import copy


def execute_BedAssessmentMultiDEM(routes, ptsfolder, outptsfolder, downstream_s, manning, messages):
    # Work as BedAssessment with the following modifications:
    # - width, zwater and Q are folders, with rasters within for each day of LiDAR acquisition (same name for the
    #   rasters of the same day in the different folders)
    # - width and Q must have values at the watershed scale
    # - zwater has value only where the DEM is available for a given day
    # - When the zwater value is found and there no zwater downstream, the normal depth is calculated at the downstream
    #   point, using the (average) slope and the (average) bed elevation of the valid downstream point result(s)
    # - The results (bed elevation) are also for each day of LiDAR acquisition, so it's a folder to.


    dict_fields = { "width":"width", "wslidar":"ws", "Q":"Q"}
    trees = build_trees(routes, "RouteID", "LENGTH_GEO")
    for tree in trees:
        print (tree)
        tree.load_multipoints(ptsfolder, "RouteID", "dist", "totald", "POINT_X", "POINT_Y", dict_fields)

    #pickle.dump(trees, open(r"D:\InfoCrue\tmp\savetreebed_bec.pkl", "wb"), protocol=2)

    #trees = pickle.load(open(r"D:\InfoCrue\tmp\savetreebed_v6.pkl", "rb"))

    # Ordering the DEMs to be processed
    # rasters can be added several times, if there are several reaches with gaps between
    #  each raster (or part of a raster) need to be fully processed before passing to the next one.
    # Let's call each of the data processing a "run". We create a list of runs, defined by a raster and a number
    #  ordering the runs. The run number is given to the csdata.
    # Meanwhile, let's check if the cs has valid data (i.e. data on at least one water surface elevation raster)
    runlist = []
    current_run_num = 0
    for tree in trees:
        for segment, prev_cs, cs in tree.browsepts():
            cs.valid_data = False
            if segment.id == 21 or segment.id == 20:
                pass
            for raster_name, csdata in cs.data_dict.items():
                if csdata.wslidar != -9999:
                    cs.valid_data = True
                    if prev_cs is None:
                        current_run_num +=1
                        runlist.append((raster_name, current_run_num))
                        csdata.run_num = current_run_num
                    else:
                        if prev_cs.data_dict[raster_name].wslidar == -9999:
                            current_run_num += 1
                            runlist.append((raster_name, current_run_num))
                            csdata.run_num = current_run_num
                        else:
                            csdata.run_num = prev_cs.data_dict[raster_name].run_num
                else:
                    csdata.run_num = 0


    print (runlist)

    # 1D hydraulic calculations
    # .wslidar: water surface measured on the LiDAR (do not change)
    # .z: bed elevation (calculated after each iteration)
    # .ws: water surface calculated at each iteration

    for raster_name, run_num in runlist:
        # iterate through each "run"
        print (raster_name)
        print (run_num)
        dem_reached = False
        results_dict = {}

        # first run: calculate downstream border condition
        for tree in trees:
            #print tree

            for segment, prev_cs, cs in tree.browsepts():

                csdata = cs.data_dict[raster_name]
                csdata.n = manning

                if csdata.run_num == run_num:
                    dem_reached = True

                # - Calculate bed elevation from other DEMs
                # - compute hydraulic with the discharge for the current DEM
                list_avg_z = []
                for otherraster_name, othercsdata in cs.data_dict.items():
                    if othercsdata.run_num != 0 and othercsdata.run_num < run_num:
                        # already treated csdata
                        list_avg_z.append(othercsdata.z)
                if len(list_avg_z) > 0:
                    prevres_csdata = copy.deepcopy(csdata)
                    cs.prevres_csdata = prevres_csdata
                    prevres_csdata.z = sum(list_avg_z) / len(list_avg_z)

                    # Apply 1D hydraulic
                    if prev_cs == None or not prev_cs.valid_data:

                        # downstream cs calculation
                        prevres_csdata.s = cs.proxy_s
                        manning_solver(prevres_csdata)
                        prevres_csdata.v = prevres_csdata.Q / (prevres_csdata.width * prevres_csdata.y)
                        prevres_csdata.h = prevres_csdata.z + prevres_csdata.y + prevres_csdata.v ** 2 / (2 * g)
                        prevres_csdata.Fr = prevres_csdata.v / (g * prevres_csdata.y) ** 0.5
                        prevres_csdata.solver = "manning"
                        prevres_csdata.type = 0

                    else:
                        cs_solver(prevres_csdata, prev_cs.prevres_csdata)
                        prevres_csdata.solver = "regular"

                        cs.proxy_s = prevres_csdata.s
                else:

                    # slope is passed through the cells, assuming a uniform flow
                    if prev_cs != None:
                        cs.proxy_s = prev_cs.proxy_s
                        if not prev_cs.valid_data and csdata.run_num == run_num:
                            # Gap: no valid data in any DEM
                            messages.addWarningMessage("Gap at " + str(cs.X) + ", " + str(cs.Y) + ". Normal depth applied based on downstream slope")

                if csdata.run_num == run_num:
                    csdata.ws = csdata.wslidar
                    csdata.z = csdata.wslidar

                if prev_cs == None:
                    cs.proxy_s = downstream_s




        for tree in trees:
            enditeration = False
            iteration = 0

            while not enditeration:
                iteration += 1


                for segment, prev_cs, cs in tree.browsepts():

                    csdata = cs.data_dict[raster_name]
                    csdata.n = manning

                    if csdata.run_num == run_num:


                        # Apply 1D hydraulic
                        if prev_cs == None or not prev_cs.valid_data or prev_cs.data_dict[raster_name].run_num == 0:

                            csdata.s = cs.proxy_s
                            manning_solver(csdata)
                            csdata.v = csdata.Q / (csdata.width * csdata.y)
                            csdata.h = csdata.z + csdata.y + csdata.v ** 2 / (2 * g)
                            csdata.Fr = csdata.v / (g * csdata.y) ** 0.5
                            csdata.solver = "manning"
                            csdata.type = 0

                        else:

                            cs_solver(csdata, prev_cs.data_dict[raster_name])
                            csdata.solver = "regular"

                        csdata.ws_before_correction = csdata.ws
                        csdata.ws = csdata.z + csdata.y
                        csdata.dif = csdata.ws - csdata.wslidar


                corrections = []
                # down to up
                for segment, prev_cs, cs in tree.browsepts():
                    csdata = cs.data_dict[raster_name]
                    if csdata.run_num == run_num:
                        if prev_cs != None and prev_cs.data_dict[raster_name].run_num == run_num:
                            prev_csdata = prev_cs.data_dict[raster_name]

                            if prev_csdata.z_fill > csdata.z:
                                if prev_csdata.z == prev_csdata.z_fill:
                                    # first backwater cell
                                    correction = []
                                    corrections.append(correction)
                                    csdata.idcorrection = len(corrections) - 1
                                else:
                                    correction = corrections[prev_csdata.idcorrection]
                                    csdata.idcorrection = prev_csdata.idcorrection
                                csdata.z_fill = prev_csdata.z_fill
                                correction.append(csdata)
                            else:
                                csdata.z_fill = csdata.z
                                correction = []
                                correction.append(csdata)
                                corrections.append(correction)
                                csdata.idcorrection = len(corrections) - 1

                        else:
                            csdata.z_fill = csdata.z
                            correction = []
                            correction.append(csdata)
                            corrections.append(correction)
                            csdata.idcorrection = len(corrections) - 1


                enditeration = True

                for correction in corrections:
                    sumdif = 0
                    sumdifws = 0
                    for cscorrect in correction:
                        sumdif += cscorrect.dif
                        sumdifws += cscorrect.ws - cscorrect.ws_before_correction

                    correcteddif = sumdif / len(correction)
                    difws = abs(sumdifws) / len(correction)
                    if difws > 0.01:
                        for cscorrect in correction:
                            cscorrect.z = cscorrect.z - correcteddif
                        enditeration = False

        print (iteration)

        tree.save_multipoints(outptsfolder, "z", arcpy.Describe(routes).spatialReference)

    return



class Messages():
    def addErrorMessage(self, text):
        print(text)

    def addWarningMessage(self, text):
        print(text)

    def addMessage(self, text):
        print(text)

if __name__ == "__main__":
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True
    messages = Messages()
    arcpy.env.scratchWorkspace = r"D:\InfoCrue\tmp"



    arcpy.env.scratchWorkspace = r"D:\InfoCrue\tmp"


    manning = 0.03


    downstream_s = 0.0001

    #frompoints = r"D:\InfoCrue\Refontebathy\Inputs\dep_pts_simp.shp"
    ptsfolder = r"D:\InfoCrue\tmp\testbed\PathPoints"
    routes = r"D:\InfoCrue\tmp\testbed\routesflowdir.shp"
    messages = Messages()

    outptsfolder = r"D:\InfoCrue\tmp\testbed\OutPoints"

    execute_BedAssessmentMultiDEM(routes, ptsfolder, outptsfolder, downstream_s, manning, messages)
