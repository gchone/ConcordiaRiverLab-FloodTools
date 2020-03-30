# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Mai 2019 - Création


import os
import arcpy
import pickle
from RasterIO import *
from tree.OurTreeSegment import *
from tree.OurTreeManager import *
#from Solver2 import *
from SolverLisflood import *


def execute_BedAssessment(r_flowdird4, str_frompoint, r_width, r_zwater, r_manning, result, r_Q, messages, picklefile = None):




    if picklefile is not None and os.path.exists(picklefile):
        pickletree = open(picklefile, 'rb')
        tree = pickle.load(pickletree)
    else:
        flowdir = RasterIO(r_flowdird4)
        zwater = RasterIO(r_zwater)
        width = RasterIO(r_width)
        Q = RasterIO(r_Q)
        manning = RasterIO(r_manning)
        # manning = r_manning
        tree = OurTreeManager()
        tree.build_tree(flowdir,str_frompoint,width=width,wslidar=zwater,n=manning,Q=Q)
        if picklefile is not None:
            pickletree = open(picklefile, 'wb')
            pickle.dump(tree, pickletree)
            pickletree.close()

    print "arbre construit"
    print tree.treeroot

    Result = RasterIO(r_flowdird4, result, float, -255)


    # A paramétrer
    #downstream_s = 0.0001
    downstream_s = 0.004

    enditeration = False
    iteration = 0
    while not enditeration:
        iteration += 1
        print iteration


        # 1D hydraulic calculations
        prevsegid = 0
        for segment, prev_cs, cs in tree.browsepts():
            #cs.n = manning
            if iteration == 1:
                cs.zlidar = cs.wslidar
                cs.ws = cs.wslidar

            if prev_cs == None:

                # downstream cs calculation
                cs.s = downstream_s
                manning_solver(cs)
                cs.v = cs.Q / (cs.width * cs.y)
                cs.h = cs.zlidar + cs.y + cs.v ** 2 / (2 * g)
                cs.Fr = cs.v / (g * cs.y) ** 0.5
                cs.solver = "manning"
                cs.type = 0


            else:
                # if prevsegid <> segment.id:
                #     print segment.id
                cs_solver(cs, prev_cs)
                #print str(cs.zlidar)+ ", " + str(cs.col) +  ", " + str(cs.row)+  ", " + str(cs.dist)

            cs.prev_ws = cs.ws
            cs.ws = cs.zlidar + cs.y
            cs.dif = cs.ws - cs.wslidar


            prevsegid = segment.id




        corrections = []
        # down to up
        for segment, prev_cs, cs in tree.browsepts():
            if prev_cs != None:
                if prev_cs.z_fill > cs.zlidar:
                    if prev_cs.zlidar == prev_cs.z_fill:
                        # first backwater cell
                        correction = []
                        corrections.append(correction)
                        cs.idcorrection = len(corrections) - 1
                    else:
                        correction = corrections[prev_cs.idcorrection]
                        cs.idcorrection = prev_cs.idcorrection
                    cs.z_fill = prev_cs.z_fill
                    correction.append(cs)
                else:
                    cs.z_fill = cs.zlidar
                    correction = []
                    correction.append(cs)
                    corrections.append(correction)
                    cs.idcorrection = len(corrections) - 1
            else:
                cs.z_fill = cs.zlidar
                correction = []
                correction.append(cs)
                corrections.append(correction)
                cs.idcorrection = len(corrections) - 1

        enditeration = True
        for correction in corrections:
            sumdif = 0
            sumdifws = 0
            for cscorrect in correction:
                sumdif += cscorrect.dif
                sumdifws += cscorrect.ws - cscorrect.prev_ws
            correcteddif = sumdif / len(correction)
            difws = abs(sumdifws) / len(correction)
            if difws > 0.01:
                for cscorrect in correction:
                    cscorrect.zlidar = cscorrect.zlidar - correcteddif
                enditeration = False


    print "Done: saving"
    for segment in tree.treesegments():
        for pt in segment.get_profile():
            Result.setValue(pt.row, pt.col, pt.zlidar)
            #Result.setValue(pt.row, pt.col, pt.Fr)

    Result.save()


    return


if __name__ == "__main__":
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True


    # frompoints = r"F:\MSP2\Mitis\EAIP2point0\Frompoints.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Mitis\EAIP2point0\flowdir")
    # width = arcpy.Raster(r"F:\MSP2\Mitis\EAIP2point1\width\wgauss100")
    # zwater = arcpy.Raster(r"F:\MSP2\Mitis\EAIP2point1\ws")
    # Q = arcpy.Raster(r"F:\MSP2\Mitis\EAIP2point0\bedassessment\qlidar")
    # result = r"F:\MSP2\Mitis\EAIP2point1\bed\depth0030"

    # arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    # frompoints = r"F:\MSP2\Yamaska\demnov18\FromPoints2.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Yamaska\demnov18\flowdir")
    # width = arcpy.Raster(r"F:\MSP2\Yamaska\demnov18\widthcalc\gauss100b")
    # zwater = arcpy.Raster(r"F:\MSP2\Yamaska\demnov18\ws\wsavg")
    # Q = arcpy.Raster(r"F:\MSP2\Yamaska\DischargeLiDAR\qlidar")
    # manning = arcpy.Raster(r"F:\MSP2\Yamaska\demnov18\n003")
    # result = r"F:\MSP2\Yamaska\tmp\testbed"

    # Input Yamaska 20m
    # arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    # frompoints = r"F:\MSP2\Yamaska\tmp\BedAssessmentFilesExample\FromPoints2.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Yamaska\tmp\BedAssessmentFilesExample\flowdir")
    # width = arcpy.Raster(r"F:\MSP2\Yamaska\tmp\BedAssessmentFilesExample\width")
    # zwater = arcpy.Raster(r"F:\MSP2\Yamaska\tmp\BedAssessmentFilesExample\wsavg")
    # Q = arcpy.Raster(r"F:\MSP2\Yamaska\tmp\BedAssessmentFilesExample\qlidar")
    # manning = arcpy.Raster(r"F:\MSP2\Yamaska\tmp\BedAssessmentFilesExample\frictioncom")
    # result = r"F:\MSP2\Yamaska\tmp\BedAssessmentFilesExample\testbed"

    # Input Yamaska 10m
    # arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    # frompoints = r"F:\MSP2\Yamaska\demnov18\resolution10m\FpInfoCrue\frompoints.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Yamaska\demnov18\resolution10m\FpInfoCrue\flowdir")
    # width = arcpy.Raster(r"F:\MSP2\Yamaska\demnov18\resolution10m\FpInfoCrue\width\wmerged")
    # zwater = arcpy.Raster(r"F:\MSP2\Yamaska\demnov18\resolution10m\FpInfoCrue\ws\ws")
    # Q = arcpy.Raster(r"F:\MSP2\Yamaska\demnov18\resolution10m\FpInfoCrue\qlidar")
    # manning = arcpy.Raster(r"F:\MSP2\Yamaska\demnov18\resolution10m\FpInfoCrue\nmanning\n003")
    # result = r"F:\MSP2\Yamaska\demnov18\resolution10m\FpInfoCrue\zbed\test"

    #
    # frompoints = r"F:\MSP2\Mastigouche\EAIP\EAIP2point1\FromPoint.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIP2point0\flowdir")
    # width = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIP2point1\gausswidth")
    # zwater = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIP2point0\wsavg")
    # Q = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIP2point1\qlidarb")
    # manning = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIP2point1\nchan3")


    arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    #frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\FromPointsGRHQ.shp"
    #frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\width\FromPointJConly.shp"
    #flowdir = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\withStreamBurning\flowdir")
    #width = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\withStreamBurning\width\width")
    # zwater origine
    #zwater = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\withStreamBurning\ws\noburnwsbr")
    # nouveau zwater test jc only
    #zwater = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\withStreamBurning\compabathy\wsr2smbr")
    #zwater = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\new1Dmodel\eaipbv_juin19\wssmbr")
    #iteration
    #zwater = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\new1Dmodel\bathyiteratif\iteratifbackwater\bed10")
    #Q = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\withStreamBurning\discharge\qlidarprop")
    #Q = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\new1Dmodel\newqlidar\qlidarht2")
    #Q = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\withStreamBurning\sensiQlidar\qlidar1000")
    #manning = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\Manning\n003ch")
    #manning = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\new1Dmodel\eaipbv_juin19\calib\nvartest")

    # frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\FromPoints.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\withStreamBurning\flowdir")
    # width = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\width\widthD4")
    # zwater = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\new1Dmodel\eaipbv_juin19\wssmbr")
    # Q = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\new1Dmodel\newqlidar\qlidarht2")
    # manning = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\Manning\n003ch")
    #
    # result = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\bed\auto1cm"

    #
    # frompoints = r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\FromPoint2.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\burnedflowdir")
    # width = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\width\wlinear")
    # #zwater = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\ws\wsbr")
    # zwater = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\depthcompa\wsr2smoothbr")
    # Q = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\qlidar")
    # manning = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\nchan3")
    # result = r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\new1Dmodel\iteratifbathy\test5cm"


    # frompoints = r"F:\MSP2\Chaudiere\fromPoint.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Chaudiere\burn\flowdir")
    # width = arcpy.Raster(r"F:\MSP2\Chaudiere\largeur\wlinear")
    # zwater = arcpy.Raster(r"F:\MSP2\Chaudiere\ws\wssmbbr")
    # Q = arcpy.Raster(r"F:\MSP2\Chaudiere\qlidar\qlidar")
    # manning = arcpy.Raster(r"F:\MSP2\Chaudiere\manning\n0028ch")
    # result = r"F:\MSP2\Chaudiere\depth\auto0028"


    #
    # frompoints = r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\FromPoint.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\burnfd_c")
    # width = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\width_c")
    # zwater = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\wssmbbr")
    # Q = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\qlidar")
    # manning = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\n0033ch_c")
    #
    #
    # result = r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\d0033_old"

    # frompoints = r"F:\MSP2\Chaudiere\fromPoint.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathySud\burnfd_cc")
    # width = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathySud\width_c")
    # zwater = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathySud\wssmbbr")
    # Q = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathySud\qlidar")
    # manning = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathySud\n003ch_c")
    #
    # result = r"F:\MSP2\Chaudiere\newDEMoct2019\bathySud\d0030_ob"


    # frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\B1\FromPointB1.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\B1\flowdirb1_10m")
    # width = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\B1\widthd4")
    # zwater = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\B1\wssmbbrb1_10m")
    # Q = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\B1\qlidar\qlidarb")
    # manning = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\B1\n003ch")
    #
    # result = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\B1\bathy003"

    # frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\FromPointsOne.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\flowdir10m_c")
    # width = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\widthd4_c")
    # zwater = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\breach10bbr_c")
    # Q = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\qlidar_c")
    # manning = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\n003ch_c")
    #
    # result = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\bathy003"

    # frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\auxPommes\FromPoint.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\auxPommes\flowdir10m_c")
    # width = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\auxPommes\widthd4")
    # zwater = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\auxPommes\breach10mbbr")
    # Q = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\auxPommes\qlidar")
    # manning = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\auxPommes\n003ch_c")
    #
    # result = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\auxPommes\bathy003"

    frompoints = r"F:\MSP2\Mitis\Fevrier2020\FromPoints.shp"
    flowdir = arcpy.Raster(r"F:\MSP2\Mitis\Fevrier2020\burn\flowdir_c")
    width = arcpy.Raster(r"F:\MSP2\Mitis\Fevrier2020\width\wlineard4")
    zwater = arcpy.Raster(r"F:\MSP2\Mitis\Fevrier2020\ws\wssmbbr")
    Q = arcpy.Raster(r"F:\MSP2\Mitis\Fevrier2020\qlidar\qlidar_c")
    manning = arcpy.Raster(r"F:\MSP2\Mitis\Fevrier2020\manning\nch003")

    result = r"F:\MSP2\Mitis\Fevrier2020\bathy\bathy003"

    #manning = 0.0175
    #picklefile = r"F:\MSP2\tmp\tree.pkl"
    #picklefile = r"F:\MSP2\Yamaska\demnov18\tree.pkl"
    print "fichiers lus"




    #result = r"F:\MSP2\Mastigouche\EAIP\EAIP2point1\depthchan3"


    execute_BedAssessment(flowdir, frompoints, width, zwater, manning, result, Q, None)
