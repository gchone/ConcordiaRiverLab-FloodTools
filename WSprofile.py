# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Février 2019 - Création

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

def execute_WSprofile(r_flowdir, str_frompoint, r_z, str_zws, str_zwssm, picklefile=None):

    if picklefile is not None and os.path.exists(picklefile):
        pickletree = open(picklefile, 'rb')
        tree = pickle.load(pickletree)
    else:
        flowdir = RasterIO(r_flowdir)
        z =  RasterIO(r_z)

        tree = OurTreeManager()
        tree.build_tree(flowdir,str_frompoint,z=z)
        if picklefile is not None:
            pickletree = open(picklefile, 'wb')
            pickle.dump(tree, pickletree)
            pickletree.close()

    print "arbre construit"
    print tree.treeroot


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



    # version sans tributaire
    # goodslope = False
    # while not goodslope:
    #     print "iteration"
    #     # down to up
    #     for segment, prev_cs, cs in tree.browsepts():
    #         if prev_cs != None:
    #             cs.z_fill = max(prev_cs.z_fill, cs.z)
    #         else:
    #             cs.z_fill = cs.z
    #     # up to down
    #     for segment, prev_cs, cs in tree.uptodown_browsepts():
    #         if prev_cs != None:
    #             cs.z_breach = min(prev_cs.z_breach, cs.z)
    #         else:
    #             cs.z_breach = cs.z
    #         if prev_cs != None:
    #             if cs.z_breach == prev_cs.z_breach and cs.z_fill == prev_cs.z_fill:
    #                 # ajout de la cs à la correction
    #                 correction.append(cs)
    #             else:
    #                 # traitement de la correction précédente
    #                 sumz2 = 0
    #                 for cscorrect in correction:
    #                     sumz2 += cscorrect.z ** 2
    #                 correctedz = (sumz2/len(correction))**0.5
    #                 for cscorrect in correction:
    #                     cscorrect.z = correctedz
    #                 # nouvelle correction
    #                 correction = []
    #                 correction.append(cs)
    #         else:
    #             correction = []
    #             correction.append(cs)
    #
    #     # pour le dernier:
    #     sumz2 = 0
    #     for cscorrect in correction:
    #         sumz2 += cscorrect.z ** 2
    #     correctedz = (sumz2 / len(correction)) ** 0.5
    #     for cscorrect in correction:
    #         cscorrect.z = correctedz
    #
    #     # test goodslope
    #     goodslope = True
    #     # up to down
    #     for segment, prev_cs, cs in tree.uptodown_browsepts():
    #         if prev_cs != None and cs.z > prev_cs.z:
    #             goodslope = False

    #




    #### Tests pas bon ####

    # # parcour depuis l'aval
    # for segment, prev_cs, cs in tree.browsepts():
    #
    #     if cs.z_breach < cs.z:
    #         # on rencontre une correction potentielle
    #
    #         z_test = cs.z_breach
    #
    #         # print "correction:"
    #         # print z_test
    #
    #         # on cherche toutes les cs possiblement concernées par z_test
    #         sumR2, nbcs = __recursivecheckcs(segment, 0, 0, z_test, cs.z_breach)
    #
    #         currentresult = sumR2
    #         #bestz = z_test
    #
    #         #print currentresult
    #
    #         z_test += 0.1
    #         sumR2, nbcs = __recursivecheckcs(segment, 0, 0, z_test, cs.z_breach)
    #         newresult = sumR2
    #
    #
    #         while newresult < currentresult:
    #             currentresult = newresult
    #             #print currentresult
    #             #bestz = z_test
    #             z_test += 0.1
    #             sumR2, nbcs = __recursivecheckcs(segment, 0, 0, z_test, cs.z_breach)
    #             newresult = sumR2
    #
    #
    #         currentresult = newresult
    #         # retour au cm près
    #         z_test -= 0.01
    #         sumR2, nbcs = __recursivecheckcs(segment, 0, 0, z_test, cs.z_breach)
    #         newresult = sumR2
    #         bestz = z_test
    #
    #
    #         while newresult < currentresult:
    #             currentresult = newresult
    #             #print currentresult
    #             bestz = z_test
    #             z_test -= 0.01
    #             sumR2, nbcs = __recursivecheckcs(segment, 0, 0, z_test, cs.z_breach)
    #             newresult = sumR2
    #
    #
    #
    #         # on met les cs affectées à l'élévation trouvée
    #         __recursivesetz(segment, bestz, cs.z_breach)
    #
    #         # on refait les breach et fill (pour les corrections nested)
    #         # up to down
    #         for segmentbr, prev_csbr, csbr in tree.uptodown_browsepts():
    #             if prev_csbr != None:
    #                 csbr.z_breach = min(prev_csbr.z_breach, csbr.z)
    #             else:
    #                 csbr.z_breach = csbr.z
    #
    #         # down to up
    #         for segmentfill, prev_csfill, csfill in tree.browsepts():
    #             if prev_csfill != None:
    #                 csfill.z_fill = max(prev_csfill.z_fill, csfill.z)
    #             else:
    #                 csfill.z_fill = csfill.z
    #

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

    # Input pour JC 10m
    arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    #flowdir = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\flowdir")
    # pour tests jc only
    # frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\width\FromPointJConly.shp"
    #frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\FromPointsGRHQ.shp"
    #z = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\dem10mcomp")
    #zws = r"F:\MSP2\JacquesCartier\newDEMmars2019\new1Dmodel\eaipbv\test3"
    #zwssm = r"F:\MSP2\JacquesCartier\newDEMmars2019\new1Dmodel\eaipbv\test4"

    # Input pour Mastigouche
    # arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    # flowdir = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\flowdir")
    # frompoints = r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\FromPoint.shp"
    # z = arcpy.Raster(r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\dem10mcompbv")
    # zws = r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\testws7"
    # zwssm = r"F:\MSP2\Mastigouche\EAIP\EAIPavril2019\testws8"

    # flowdir = arcpy.Raster(r"F:\MSP2\Chaudiere\noburn\flowdir")
    # frompoints = r"F:\MSP2\Chaudiere\fromPoint.shp"
    # z = arcpy.Raster(r"F:\MSP2\Chaudiere\dem10m")
    # zws = r"F:\MSP2\Chaudiere\ws\wsraw"
    # zwssm = r"F:\MSP2\Chaudiere\ws\wssm"

    # flowdir = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\flowdir")
    # frompoints = r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\FromPoint.shp"
    # z = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\DEM\nord10m_noh")
    # zws = r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\wsraw"
    # zwssm = r"F:\MSP2\Chaudiere\newDEMoct2019\bathyNord\wssm"

    # flowdir = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\bathySud\flowdir")
    # frompoints = r"F:\MSP2\Chaudiere\fromPoint.shp"
    # z = arcpy.Raster(r"F:\MSP2\Chaudiere\newDEMoct2019\DEM\cehq10m_nob")
    # zws = r"F:\MSP2\Chaudiere\newDEMoct2019\bathySud\wsraw"
    # zwssm = r"F:\MSP2\Chaudiere\newDEMoct2019\bathySud\wssm"

    # SGC amont
    # flowdir = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\flowdirb1")
    # frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\FromPointB1.shp"
    # z = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\lidar1mb1")
    # zws = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\wsrawb1"
    # zwssm = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\wssmb1"

    # flowdir = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\flowdir1m")
    # frompoints = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\FromPoints.shp"
    # z = arcpy.Raster(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\dem1m_c_p")
    # zws = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\wsraw"
    # zwssm = r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\SubGC\StJoseph\wssm"



    flowdir = arcpy.Raster(r"F:\MSP2\Mitis\Fevrier2020\notburn\flowdir_c")
    frompoints = r"F:\MSP2\Mitis\Fevrier2020\FromPoints.shp"
    z = arcpy.Raster(r"F:\MSP2\Mitis\EAIPsept2019\DEMs\compound10m")
    zws = r"F:\MSP2\Mitis\Fevrier2020\ws\wsraw"
    zwssm = r"F:\MSP2\Mitis\Fevrier2020\ws\wssm"

    print "fichiers lus"



    execute_WSprofile(flowdir, frompoints, z, zws, zwssm, None)
