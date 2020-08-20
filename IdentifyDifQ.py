# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Août 2020 - Création


import os
import arcpy
from RasterIO import *
from tree.OurTreeSegment import *
from tree.OurTreeManager import *



def execute_IdentifyDifQ(r_flowdir, str_frompoint, r_flowacc, increase, result_pts, messages):



    flowdir = RasterIO(r_flowdir)
    flowacc = RasterIO(r_flowacc)

    trees = build_trees(flowdir, str_frompoint, flowacc=flowacc)

    # Nouvelle FeatureClass pour les points
    arcpy.CreateFeatureclass_management(os.path.dirname(result_pts),
                                        os.path.basename(result_pts), "POINT",
                                        spatial_reference=r_flowdir)
    pointcursor = arcpy.da.InsertCursor(result_pts, "SHAPE@XY")

    for tree in trees:

        # down to up
        for segment, prev_cs, cs in tree.browsepts():
            if prev_cs is not None:
                if prev_cs.flowacc > (cs.flowacc*(1+increase)):
                    pointcursor.insertRow([(flowdir.ColtoX(cs.col), flowdir.RowtoY(cs.row))])

    return



