# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v2.0 - Février 2019 - Création
# v2.1 - Septembre 1019 - Code ré-écrit pour plus de clarté

import os
import arcpy
import pickle
from RasterIO import *
from tree.OurTreeSegment import *
from tree.OurTreeManager import *




def execute_QfromHydrotel(r_flowdir, str_frompoint, r_flowacc, r_qpts, str_res, interpolation, picklefile=None):



    if picklefile is not None and os.path.exists(picklefile):
        pickletree = open(picklefile, 'rb')
        tree = pickle.load(pickletree)
    else:
        flowdir = RasterIO(r_flowdir)
        flowacc = RasterIO(r_flowacc)
        qpts = RasterIO(r_qpts)

        tree = OurTreeManager()
        tree.build_tree(flowdir,str_frompoint,Q=qpts,flowacc=flowacc)
        if picklefile is not None:
            pickletree = open(picklefile, 'wb')
            pickle.dump(tree, pickletree)
            pickletree.close()

    print "arbre construit"
    print tree.treeroot


    # transmitting from upstream point
    for segment, prev_cs, cs in tree.uptodown_browsepts():

        cs.A = float(cs.flowacc)


        if cs.Q <> qpts.nodata:
            cs.up_ptsA = cs.A
            cs.up_ptsQ = cs.Q
        elif prev_cs != None:
            cs.up_ptsA = prev_cs.up_ptsA
            cs.up_ptsQ = prev_cs.up_ptsQ
        else:
            cs.up_ptsA = 0
            cs.up_ptsQ = 0

    # transmitting from downstream point
    for segment, prev_cs, cs in tree.browsepts():


        if cs.Q <> qpts.nodata:
            cs.down_ptsA = cs.A
            cs.down_ptsQ = cs.Q

        else:
            if prev_cs != None:
                cs.down_ptsA = prev_cs.down_ptsA
                cs.down_ptsQ = prev_cs.down_ptsQ
            else:
                cs.down_ptsA = 0
                cs.down_ptsQ = 0

            if interpolation:
                cs.alpha = (cs.up_ptsQ - cs.down_ptsQ) / (cs.up_ptsA - cs.down_ptsA)
                cs.beta = cs.down_ptsQ - cs.alpha * cs.down_ptsA
                cs.Q = cs.alpha * cs.A + cs.beta
            else:
                if cs.down_ptsA == 0:
                    # cas particulier : pas d'interpolation (débit de crue), et extrapolation down
                    cs.Q = cs.up_ptsQ/cs.up_ptsA*cs.A
                else:
                    cs.Q = cs.down_ptsQ/cs.down_ptsA*cs.A



    Res = RasterIO(r_flowdir, str_res, float, -255)

    for segment in tree.treesegments():
        for pt in segment.get_profile():
            Res.setValue(pt.row, pt.col, pt.Q)

    Res.save()


    return


if __name__ == "__main__":
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True

    # if interpolation is False, Q is proportional to the drainage area, based on the closest downstream data point
    #   (or the closest upstream data point if no downstream data point exists)
    # if interpolation is True, a function Q= alpha*Area + beta is constructed between two data points (the closest
    #   upstream and downstream). Q is proportional to the drainage area based on the closest downstream data point if
    #   no upstream data point exists, or based on the closest upstream data point if no downstream data point exists.

    # # Chaudière : Débit LiDAR
    # arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    # frompoints = r"F:\MSP2\Chaudiere\fromPoint.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Chaudiere\burn\flowdir")
    # flowacc = arcpy.Raster(r"F:\MSP2\Chaudiere\burn\flowacc")
    # qpts = arcpy.Raster(r"F:\MSP2\Chaudiere\qlidar\qmoyhtpts")
    # interpolation = True
    # qresult = r"F:\MSP2\Chaudiere\qlidar\qmoyinterpol"

    # Chaudière : Débit de crue
    # arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    # frompoints = r"F:\MSP2\Chaudiere\fromPoint.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Chaudiere\burn\flowdir")
    # flowacc = arcpy.Raster(r"F:\MSP2\Chaudiere\burn\flowacc")
    # qpts = arcpy.Raster(r"F:\MSP2\Chaudiere\qflood\q100_90sta")
    # interpolation = False
    # qresult = r"F:\MSP2\Chaudiere\qflood\q100_90inter"

    arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    # frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\FromPoints.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\withStreamBurning\flowdir")
    # flowacc = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\withStreamBurning\flowacc")
    # qpts = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\discharges\q100ptsc_90p")
    # interpolation = False
    # qresult = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\discharges\q100ht_90p"

    arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    # frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StreamBurningFullNetwork\FromPoints.shp"
    # flowdir = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StreamBurningFullNetwork\flowdir")
    # flowacc = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StreamBurningFullNetwork\flowacc")
    # qpts = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StreamBurningFullNetwork\qlidar\qmedatpts")
    # interpolation = True
    # qresult = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StreamBurningFullNetwork\qlidar\qmedlin"

    frompoints = r"F:\MSP2\Mitis\Fevrier2020\qhydrotel2018\fp_flood.shp"
    flowdir = arcpy.Raster(r"F:\MSP2\Mitis\Fevrier2020\burn\flowdir")
    flowacc = arcpy.Raster(r"F:\MSP2\Mitis\Fevrier2020\burn\flowacc")
    qpts = arcpy.Raster(r"F:\MSP2\Mitis\Fevrier2020\qhydrotel2018\r_q350")
    interpolation = False
    qresult = r"F:\MSP2\Mitis\Fevrier2020\qhydrotel2018\q350"


    print "fichiers lus"





    execute_QfromHydrotel(flowdir, frompoints, flowacc, qpts, qresult, interpolation, None)
