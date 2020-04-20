# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Février 2019 - Création
# v1.1 - Avril 2020 - Ajout de lissage seulement

import os
import arcpy
import pickle
from RasterIO import *
from tree.OurTreeSegment import *
from tree.OurTreeManager import *


def __recursivecheckcs(segment, sumR2, nbcs, z_test, cs_z_breach):
    for checkcs in segment.get_profile():
        if checkcs.z_breach <= z_test and checkcs.z_breach >= cs_z_breach:
            sumR2 += (checkcs.z - z_test) ** 2
            nbcs += 1
            if checkcs == segment.get_profile()[-1]:
                # si la dernière cs du segment est incluse, il faut continuer sur les segments amont
                for child in segment.get_childrens():
                    sumR2, nbcs = __recursivecheckcs(child, sumR2, nbcs, z_test, cs_z_breach)
    return sumR2, nbcs

def __recursivesetz(segment, bestz, cs_z_breach):
    for checkcs in segment.get_profile():
        if checkcs.z_breach <= bestz and checkcs.z_breach >= cs_z_breach:
            checkcs.z = bestz
            if checkcs == segment.get_profile()[-1]:
                # si la dernière cs du segment est incluse, il faut continuer sur les segments amont
                for child in segment.get_childrens():
                    __recursivesetz(child, bestz, cs_z_breach)

def execute_WSprofile(r_flowdir, str_frompoint, r_z, str_zws, str_zwssm, smoothonly = False, r_zerr=None, picklefile=None):

    if picklefile is not None and os.path.exists(picklefile):
        pickletree = open(picklefile, 'rb')
        tree = pickle.load(pickletree)
    else:
        flowdir = RasterIO(r_flowdir)
        z =  RasterIO(r_z)

        tree = OurTreeManager()
        if not smoothonly:
            tree.build_tree(flowdir,str_frompoint,z=z)
        else:
            zerr = RasterIO(r_zerr)
            tree.build_tree(flowdir, str_frompoint, z=zerr, ztosmooth = z)
        if picklefile is not None:
            pickletree = open(picklefile, 'wb')
            pickle.dump(tree, pickletree)
            pickletree.close()

    print "arbre construit"
    print tree.treeroot

    if not smoothonly:

        goodslope = False
        iteration = 0
        while not goodslope:

            print "iteration"
            iteration += 1
            corrections = []
            # down to up
            for segment, prev_cs, cs in tree.browsepts():
                if prev_cs != None:
                    cs.z_fill = max(prev_cs.z_fill, cs.z)
                else:
                    cs.z_fill = cs.z
                if iteration == 1:
                    cs.originalfill = cs.z_fill
                # z_breach à None permet le bon breach pour les parties parcourues plusieurs fois
                cs.z_breach = None
            # up to down
            for segment, prev_cs, cs in tree.uptodown_browsepts():
                if prev_cs != None:
                    if cs.z_breach != None:
                        cs.z_breach = min(prev_cs.z_breach, cs.z, cs.z_breach)
                    else:
                        cs.z_breach = min(prev_cs.z_breach, cs.z)
                else:
                    cs.z_breach = cs.z
                if iteration == 1:
                    cs.originalbreach = cs.z_breach

            # down to up
            for segment, prev_cs, cs in tree.browsepts():
                if prev_cs != None:
                    if cs.z_breach == prev_cs.z_breach and cs.z_fill == prev_cs.z_fill:
                        # ajout de la cs à la correction
                        correction = corrections[prev_cs.idcorrection]
                        correction.append(cs)
                        cs.idcorrection = prev_cs.idcorrection
                    else:
                        # nouvelle correction
                        correction = []
                        correction.append(cs)
                        corrections.append(correction)
                        cs.idcorrection = len(corrections) - 1
                else:
                    correction = []
                    correction.append(cs)
                    corrections.append(correction)
                    cs.idcorrection = len(corrections) - 1


            for correction in corrections:
                sumz2 = 0
                for cscorrect in correction:
                    sumz2 += cscorrect.z ** 2
                correctedz = (sumz2 / len(correction)) ** 0.5
                for cscorrect in correction:
                    cscorrect.z = correctedz

            print len(corrections)

            # test goodslope
            goodslope = True
            # up to down
            for segment, prev_cs, cs in tree.uptodown_browsepts():
                if prev_cs != None and cs.z > prev_cs.z:
                    goodslope = False
                    #print cs.z
            # if len(corrections) == 4844:
            #     goodslope = True

    else:
        for segment, prev_cs, cs in tree.browsepts():
            if prev_cs != None:
                cs.z_fill = max(prev_cs.z_fill, cs.z)
            else:
                cs.z_fill = cs.z
            cs.originalfill = cs.z_fill
            # z_breach à None permet le bon breach pour les parties parcourues plusieurs fois
            cs.z_breach = None
        # up to down
        for segment, prev_cs, cs in tree.uptodown_browsepts():
            if prev_cs != None:
                if cs.z_breach != None:
                    cs.z_breach = min(prev_cs.z_breach, cs.z, cs.z_breach)
                else:
                    cs.z_breach = min(prev_cs.z_breach, cs.z)
            else:
                cs.z_breach = cs.z
            cs.originalbreach = cs.z_breach
        for segment, prev_cs, cs in tree.browsepts():
            cs.z = cs.ztosmooth

    # smoothing
    smooth_perc = 0.9
    # down to up
    for segment, prev_cs, cs in tree.browsepts():
        if prev_cs != None:
            cs.zsmooth2 = (1-smooth_perc)*cs.z + smooth_perc*max(prev_cs.zsmooth2, cs.originalbreach)
        else:
            cs.zsmooth2 = cs.z
    # up to down
    for segment, prev_cs, cs in tree.uptodown_browsepts():
        if prev_cs != None:
            if hasattr(cs, "zsmooth1"):
                cs.zsmooth1 = min((1 - smooth_perc) * cs.z + smooth_perc * min(prev_cs.zsmooth1, cs.originalfill), cs.zsmooth1)
            else:
                cs.zsmooth1 = (1-smooth_perc)*cs.z + smooth_perc*min(prev_cs.zsmooth1, cs.originalfill)
        else:
            cs.zsmooth1 = cs.z
        cs.zsmooth = (cs.zsmooth1 + cs.zsmooth2)/2
        #print str(cs.z)+" "+str(cs.zsmooth1)+" "+str(cs.zsmooth2)+" "+str(cs.zsmooth)



    zws = RasterIO(r_flowdir, str_zws, float, -255)
    zwssm = RasterIO(r_flowdir, str_zwssm, float, -255)


    for segment in tree.treesegments():
        for pt in segment.get_profile():
            zws.setValue(pt.row, pt.col, pt.z)
            zwssm.setValue(pt.row, pt.col, pt.zsmooth)

    zws.save()
    zwssm.save()
    return


if __name__ == "__main__":
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True

    #picklefile = r"F:\MSP2\tmp\picklewsjc4.pkl"


    arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"

    flowdir = arcpy.Raster(r"F:\MSP2\Mastigouche\FLTws\NewPolygons\flt5mmin_fd")
    frompoints = r"F:\MSP2\Mastigouche\FLTws\NewPolygons\FromPoint.shp"
    z = arcpy.Raster(r"F:\MSP2\Mastigouche\FLTws\NewPolygons\flt5mmin_f")
    zerr = arcpy.Raster(r"F:\MSP2\Mastigouche\FLTws\NewPolygons\dem5mmin")
    zws = r"F:\MSP2\Mastigouche\FLTws\NewPolygons\flt5mmincopy"
    zwssm = r"F:\MSP2\Mastigouche\FLTws\NewPolygons\flt5mminsm"

    print "fichiers lus"



    execute_WSprofile(flowdir, frompoints, z, zws, zwssm, True, zerr, None)
