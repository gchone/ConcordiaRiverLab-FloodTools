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
# v1.2 - Juin 2020 - Création de l'interface et suppression du lissage

import os
import arcpy
from RasterIO import *
from tree.OurTreeSegment import *
from tree.OurTreeManager import *



def execute_WSprofile(r_flowdir, str_frompoint, r_z, str_zws, messages):



    flowdir = RasterIO(r_flowdir)
    z =  RasterIO(r_z)

    trees = build_trees(flowdir, str_frompoint, z=z)

    zws = RasterIO(r_flowdir, str_zws, float, -255)

    for tree in trees:
        goodslope = False
        iteration = 0
        while not goodslope:

            iteration += 1
            corrections = []
            # down to up
            for segment, prev_cs, cs in tree.browsepts():
                if prev_cs is not None:
                    cs.z_fill = max(prev_cs.z_fill, cs.z)
                else:
                    cs.z_fill = cs.z
                if iteration == 1:
                    cs.originalfill = cs.z_fill
                # z_breach à None permet le bon breach pour les parties parcourues plusieurs fois
                cs.z_breach = None
            # up to down
            for segment, prev_cs, cs in tree.uptodown_browsepts():
                if prev_cs is not None:
                    if cs.z_breach is not None:
                        cs.z_breach = min(prev_cs.z_breach, cs.z, cs.z_breach)
                    else:
                        cs.z_breach = min(prev_cs.z_breach, cs.z)
                else:
                    cs.z_breach = cs.z
                if iteration == 1:
                    cs.originalbreach = cs.z_breach

            # down to up
            for segment, prev_cs, cs in tree.browsepts():
                if prev_cs is not None:
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

            # test goodslope
            goodslope = True
            # up to down
            for segment, prev_cs, cs in tree.uptodown_browsepts():
                if prev_cs != None and cs.z > prev_cs.z:
                    goodslope = False




        for segment in tree.treesegments():
            for pt in segment.get_profile():
                zws.setValue(pt.row, pt.col, pt.z)


    zws.save()

    return



