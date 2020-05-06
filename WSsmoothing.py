# coding: latin-1

#####################################################
# Gu�nol� Chon�
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Avril 2020 - Cr�ation. Smoothing s�par� de la fonction WSprofile. Rendu ind�pendant de la r�solution du DEM.
#       Param�trage du degr� de lissage.


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
        # z_breach � None permet le bon breach pour les parties parcourues plusieurs fois
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


    # ind�pendance par rapport � la r�solution:
    #   La m�thode de base pond�re le r�sultat final en fonction de la valeur au point et de la valeur pr�c�dente
    #   (major�e/minor�e par le fill ou le breach). L'ind�pendance par rapport � la r�solution est faire en corrigeant
    #   le poid par la puissance du ratio des distances. Le poid de base �tait pens� pour une r�solution de 10m.
    #   Ex : R�solution de 2m. On parcourt 5 pixels pour l'�quivalent de un pixel � 10m. Si le poid est de 0.9
    #   pour 10m), z = 0.9z, dans le cas d'une chute � 0 (profil en forme de marche), il faut � 2m de r�solution
    #   z*poid^5 pour avoir l'�quivalent, donc poid^5=0.9, donc poid=0.9^(1/5)
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

