# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Avril 2020 - Création. Smoothing séparé de la fonction WSprofile. Rendu indépendant de la résolution du DEM.
#       Paramétrage du degré de lissage.


import os
import arcpy
import pickle
from RasterIO import *
from tree.OurTreeSegment import *
from tree.OurTreeManager import *




def execute_WSsmoothing(r_flowdir, str_frompoint, r_z, r_zerr, str_zwssm, smooth_perc = 0.9, picklefile=None):

    if picklefile is not None and os.path.exists(picklefile):
        pickletree = open(picklefile, 'rb')
        tree = pickle.load(pickletree)
    else:
        flowdir = RasterIO(r_flowdir)
        z =  RasterIO(r_z)

        tree = OurTreeManager()


        zerr = RasterIO(r_zerr)
        tree.build_tree(flowdir, str_frompoint, zerr=zerr, ztosmooth = z)

        if picklefile is not None:
            pickletree = open(picklefile, 'wb')
            pickle.dump(tree, pickletree)
            pickletree.close()

    print "arbre construit"
    print tree.treeroot



    for segment, prev_cs, cs in tree.browsepts():
        if prev_cs != None:
            cs.z_fill = max(prev_cs.z_fill, cs.zerr)
        else:
            cs.z_fill = cs.zerr
        # z_breach à None permet le bon breach pour les parties parcourues plusieurs fois
        cs.z_breach = None
    # up to down
    for segment, prev_cs, cs in tree.uptodown_browsepts():
        if prev_cs != None:
            if cs.z_breach != None:
                cs.z_breach = min(prev_cs.z_breach, cs.zerr, cs.z_breach)
            else:
                cs.z_breach = min(prev_cs.z_breach, cs.zerr)
        else:
            cs.z_breach = cs.zerr


    # # original smoothing
    # smooth_perc = 0.9
    # # down to up
    # for segment, prev_cs, cs in tree.browsepts():
    #     if prev_cs != None:
    #         cs.zsmooth2 = (1-smooth_perc)*cs.ztosmooth + smooth_perc*max(prev_cs.zsmooth2, cs.z_breach)
    #     else:
    #         cs.zsmooth2 = cs.ztosmooth
    # # up to down
    # for segment, prev_cs, cs in tree.uptodown_browsepts():
    #     if prev_cs != None:
    #         if hasattr(cs, "zsmooth1"):
    #             cs.zsmooth1 = min((1 - smooth_perc) * cs.ztosmooth + smooth_perc * min(prev_cs.zsmooth1, cs.z_fill), cs.zsmooth1)
    #         else:
    #             cs.zsmooth1 = (1-smooth_perc)*cs.ztosmooth + smooth_perc*min(prev_cs.zsmooth1, cs.z_fill)
    #     else:
    #         cs.zsmooth1 = cs.ztosmooth
    #     cs.zsmooth = (cs.zsmooth1 + cs.zsmooth2)/2


    # indépendance par rapport à la résolution:
    #   La méthode de base pondère le résultat final en fonction de la valeur au point et de la valeur précédente
    #   (majorée/minorée par le fill ou le breach). L'indépendance par rapport à la résolution est faire en corrigeant
    #   le poid par la puissance du ratio des distances. Le poid de base était pensé pour une résolution de 10m.
    #   Ex : Résolution de 2m. On parcourt 5 pixels pour l'équivalent de un pixel à 10m. Si le poid est de 0.9
    #   pour 10m), z = 0.9z, dans le cas d'une chute à 0 (profil en forme de marche), il faut à 2m de résolution
    #   z*poid^5 pour avoir l'équivalent, donc poid^5=0.9, donc poid=0.9^(1/5)
    # down to up
    for segment, prev_cs, cs in tree.browsepts():
        if prev_cs != None:

            cs.zsmooth2 = (1-smooth_perc**(cs.dist/10.))*cs.ztosmooth + smooth_perc**(cs.dist/10.)*max(prev_cs.zsmooth2, cs.z_breach)
        else:
            cs.zsmooth2 = cs.ztosmooth
    # up to down
    for segment, prev_cs, cs in tree.uptodown_browsepts():
        if prev_cs != None:
            if hasattr(cs, "zsmooth1"):
                cs.zsmooth1 = min((1 - smooth_perc**(cs.dist/10.)) * cs.ztosmooth + smooth_perc**(cs.dist/10.) * min(prev_cs.zsmooth1, cs.z_fill), cs.zsmooth1)
            else:
                cs.zsmooth1 = (1-smooth_perc**(cs.dist/10.))*cs.ztosmooth + smooth_perc**(cs.dist/10.)*min(prev_cs.zsmooth1, cs.z_fill)
        else:
            cs.zsmooth1 = cs.ztosmooth
        cs.zsmooth = (cs.zsmooth1 + cs.zsmooth2)/2


    zwssm = RasterIO(r_flowdir, str_zwssm, float, -255)


    for segment in tree.treesegments():
        for pt in segment.get_profile():

            zwssm.setValue(pt.row, pt.col, pt.zsmooth)


    zwssm.save()
    return

