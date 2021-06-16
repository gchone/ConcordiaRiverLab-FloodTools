# coding: latin-1



import os
import arcpy

from tree.RiverNetwork import *




def execute_WSsmoothing(network_shp, links_table, RID_field, datapoints, id_field_pts, RID_field_pts, Distance_field_pts, offset_field_pts, X_field_pts, Y_field_pts, dem_z_field, dem_fill_field, output_points, smooth_perc = 0.9):

    network = RiverNetwork()
    network.dict_attr_fields['id'] = RID_field
    network.load_data(network_shp, links_table)

    collection = Points_collection(network, "data")
    collection.dict_attr_fields['id'] = id_field_pts
    collection.dict_attr_fields['reach_id'] = RID_field_pts
    collection.dict_attr_fields['dist'] = Distance_field_pts
    collection.dict_attr_fields['offset'] = offset_field_pts
    collection.dict_attr_fields['X'] = X_field_pts
    collection.dict_attr_fields['Y'] = Y_field_pts
    collection.dict_attr_fields['zerr'] = dem_z_field
    collection.dict_attr_fields['ztosmooth'] = dem_fill_field
    collection.load_table(datapoints)


    for reach in network.browse_reaches_down_to_up():
        if reach.is_downstream_end():
            prev_cs = None
        for cs in reach.browse_points(collection):
            if prev_cs != None:
                cs.z_fill = max(prev_cs.z_fill, cs.zerr)
            else:
                cs.z_fill = cs.zerr
            # z_breach à None permet le bon breach pour les parties parcourues plusieurs fois
            cs.z_breach = None
            prev_cs = cs

    # up to down
    for reach in network.browse_reaches_up_to_down():
        if reach.is_upstream_end():
            prev_cs = None
        for cs in reach.browse_points(collection, orientation="UP_TO_DOWN"):
            if prev_cs != None:
                if cs.z_breach != None:
                    cs.z_breach = min(prev_cs.z_breach, cs.zerr, cs.z_breach)
                else:
                    cs.z_breach = min(prev_cs.z_breach, cs.zerr)
            else:
                cs.z_breach = cs.zerr
            prev_cs = cs

    # indépendance par rapport à la résolution:
    #   La méthode de base pondère le résultat final en fonction de la valeur au point et de la valeur précédente
    #   (majorée/minorée par le fill ou le breach). L'indépendance par rapport à la résolution est faire en corrigeant
    #   le poid par la puissance du ratio des distances. Le poid de base était pensé pour une résolution de 10m.
    #   Ex : Résolution de 2m. On parcourt 5 pixels pour l'équivalent de un pixel à 10m. Si le poid est de 0.9
    #   pour 10m), z = 0.9z, dans le cas d'une chute à 0 (profil en forme de marche), il faut à 2m de résolution
    #   z*poid^5 pour avoir l'équivalent, donc poid^5=0.9, donc poid=0.9^(1/5)
    # down to up

    for reach in network.browse_reaches_down_to_up():

        if reach.is_downstream_end():
            prev_cs = None
        for cs in reach.browse_points(collection):
            if prev_cs != None:
                if prev_cs.reach == cs.reach:
                    localdist = (cs.dist - prev_cs.dist)
                else:
                    localdist = prev_cs.reach.length - prev_cs.dist + cs.dist

                cs.zsmooth2 = max(((1 - smooth_perc ** (localdist / 10.)) * cs.ztosmooth + smooth_perc ** (localdist / 10.) * prev_cs.zsmooth2), cs.z_breach)

            else:
                cs.zsmooth2 = cs.ztosmooth
            prev_cs = cs
    # up to down
    for reach in network.browse_reaches_up_to_down():
        if reach.is_upstream_end():
            prev_cs = None
        for cs in reach.browse_points(collection, orientation="UP_TO_DOWN"):
            if prev_cs != None:
                if prev_cs.reach == cs.reach:
                    localdist = (prev_cs.dist - cs.dist)
                else:
                    localdist = cs.reach.length - cs.dist + prev_cs.dist
                if hasattr(cs, "zsmooth1"):
                    cs.zsmooth1 = min((
                        (1 - smooth_perc ** (localdist / 10.)) * cs.ztosmooth + smooth_perc ** (localdist / 10.) *
                            prev_cs.zsmooth1), cs.z_fill, cs.zsmooth1)
                else:
                    cs.zsmooth1 = min(((1 - smooth_perc ** (localdist / 10.)) * cs.ztosmooth + smooth_perc ** (localdist / 10.) * prev_cs.zsmooth1), cs.z_fill)
            else:
                cs.zsmooth1 = cs.ztosmooth
            cs.zsmooth = (cs.zsmooth1 + cs.zsmooth2)/2.
            prev_cs = cs

    collection.add_SavedVariable("zsmooth", "float")
    collection.save_points(output_points)

    return

