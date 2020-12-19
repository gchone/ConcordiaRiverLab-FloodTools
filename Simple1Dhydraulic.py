# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Dec 2020 - Création


import os
import arcpy
import pickle
from RasterIO import *
from tree.OurTreeSegment import *
from tree.OurTreeManager import *
#from Solver2 import *
from SolverLisflood import *


def execute_Simple1Dhydraulic(r_flowdir, str_frompoint, r_width, r_zbed, manning, result, r_Q, downstream_s, messages):



    flowdir = RasterIO(r_flowdir)
    zbed = RasterIO(r_zbed)
    width = RasterIO(r_width)
    Q = RasterIO(r_Q)


    trees = build_trees(flowdir, str_frompoint, width=width, z=zbed, Q=Q)


    Result = RasterIO(r_flowdir, result, float, -255)


    for tree in trees:
        downstream_end = True
        # 1D hydraulic calculations
        for segment, prev_cs, cs in tree.browsepts():

            if (cs.width == width.nodata or cs.z==zbed.nodata or cs.Q == Q.nodata):
                cs.skipped = True
                if not downstream_end:
                    messages.addErrorMessage("Missing data at "+str(cs.X)+", "+str(cs.Y))
            else:
                cs.skipped = False
                downstream_end = False
                cs.n = manning

                if prev_cs == None or prev_cs.skipped:

                    # downstream cs calculation
                    cs.s = downstream_s
                    manning_solver(cs)
                    cs.v = cs.Q / (cs.width * cs.y)
                    cs.h = cs.z + cs.y + cs.v ** 2 / (2 * g)
                    cs.Fr = cs.v / (g * cs.y) ** 0.5
                    cs.solver = "manning"
                    cs.type = 0


                else:

                    cs_solver(cs, prev_cs)

                cs.ws = cs.z + cs.y


        for segment in tree.treesegments():
            for pt in segment.get_profile():
                if not pt.skipped:
                    Result.setValue(pt.row, pt.col, pt.ws)


    Result.save()


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

    arcpy.env.scratchWorkspace = r"D:\InfoCrue\tmp"

    str_frompoint = r"Z:\Projects\MSP\Etchemin\LisfloodJuly2020\dep_pts.shp"
    r_flowdir = arcpy.Raster(r"Z:\Projects\MSP\Etchemin\LisfloodJuly2020\d4fd")
    r_width = arcpy.Raster(r"Z:\Projects\MSP\Etchemin\LivraisonSeptembre2020\données_modèle\largeur")
    r_zbed = arcpy.Raster(r"Z:\Projects\MSP\Etchemin\LivraisonSeptembre2020\données_modèle\élévation_lit")
    r_Q = arcpy.Raster(r"D:\InfoCrue\Etchemin\q20b")
    manning = 0.03
    downstream_s = 0.0001
    result = r"D:\InfoCrue\tmp\test1dhydro"

    messages = Messages()

    execute_Simple1Dhydraulic(r_flowdir, str_frompoint, r_width, r_zbed, manning, result, r_Q, downstream_s, messages)
