# -*- coding: utf-8 -*-


# ArcGIS tools for tree manipulation
import arcpy
import numpy as np

from tree.RiverNetwork import *

def execute_InterpolatePoints(points_table, id_field_pts, RID_field_pts, Distance_field_pts, offset_field_pts, data_fields, targetpoints, id_field_target, RID_field_target, Distance_field_target, offset_field_target, network_shp, links_table, network_RID_field, order_field, ouput_table):
    network = RiverNetwork()
    network.dict_attr_fields['id'] = network_RID_field
    network.dict_attr_fields['order'] = order_field
    network.load_data(network_shp, links_table)

    datacollection = Points_collection(network, "data")
    datacollection.dict_attr_fields['id'] = id_field_pts
    datacollection.dict_attr_fields['reach_id'] = RID_field_pts
    datacollection.dict_attr_fields['dist'] = Distance_field_pts
    datacollection.dict_attr_fields['offset'] = offset_field_pts
    for field in data_fields:
        datacollection.dict_attr_fields[field] = field
    datacollection.load_table(points_table)

    targetcollection = Points_collection(network, "target")
    targetcollection.dict_attr_fields['id'] = id_field_target
    targetcollection.dict_attr_fields['reach_id'] = RID_field_target
    targetcollection.dict_attr_fields['dist'] = Distance_field_target
    targetcollection.dict_attr_fields['offset'] = offset_field_target
    targetcollection.load_table(targetpoints)

    # Gather metadata for the new array
    newdtype = []
    idfield = None

    dict_attr_output_fields = targetcollection.dict_attr_fields.copy()

    for attr, field in dict_attr_output_fields.items():
        newdtype.append((str(field), targetcollection._numpyarray.dtype.fields[targetcollection.dict_attr_fields[attr]][0]))
    for field in data_fields:
        newdtype.append(
            (str(field), datacollection._numpyarray.dtype.fields[datacollection.dict_attr_fields[attr]][0]))


    newarray = None

    for reach in network.browse_reaches_down_to_up():
        targetdata = np.sort(
            targetcollection._numpyarray[
                targetcollection._numpyarray[targetcollection.dict_attr_fields['reach_id']] == reach.id],
            order=targetcollection.dict_attr_fields['dist'])
        sorteddata = np.sort(
            datacollection._numpyarray[
                datacollection._numpyarray[datacollection.dict_attr_fields['reach_id']] == reach.id],
            order=datacollection.dict_attr_fields['dist'])

        if not reach.is_downstream_end():
            # add the most upstream point in the downstream reach in the data
            down_reach = reach.get_downstream_reach()
            downdata = np.sort(
                datacollection._numpyarray[
                    datacollection._numpyarray[datacollection.dict_attr_fields['reach_id']] == down_reach.id],
                order=datacollection.dict_attr_fields['dist'])[-1]
            # update the distance
            downdata[datacollection.dict_attr_fields['dist']] = downdata[datacollection.dict_attr_fields['dist']] - down_reach.length
            sorteddata = np.concatenate(([downdata], sorteddata))

        if not reach.is_upstream_end():
            # add the most downstream point in the upstream reach in the data
            min_order = 9999
            selected_up_reach = None
            for up_reach in reach.get_uptream_reaches():
                # the upstream reach to use is the one with the smallest order
                if up_reach.order < min_order:
                    min_order = up_reach.order
                    selected_up_reach = up_reach

            updata = np.sort(
                datacollection._numpyarray[
                    datacollection._numpyarray[datacollection.dict_attr_fields['reach_id']] == selected_up_reach.id],
                order=datacollection.dict_attr_fields['dist'])[0]
            # update the distance
            updata[datacollection.dict_attr_fields['dist']] = updata[datacollection.dict_attr_fields['dist']] + reach.length
            sorteddata = np.concatenate((sorteddata, [updata]))

        newres = np.empty(targetdata.shape[0], dtype=newdtype)

        for field, value in dict_attr_output_fields.items():
            newres[value] = targetdata[targetcollection.dict_attr_fields[field]]
        for field in data_fields:
            interp= np.interp(targetdata[targetcollection.dict_attr_fields['dist']], sorteddata[datacollection.dict_attr_fields['dist']], sorteddata[field])
            newres[field] = interp

        # Create a new array or update it
        if newarray is None:
            newarray = np.copy(newres)
        else:
            newarray = np.concatenate((newarray, newres))

    arcpy.da.NumPyArrayToTable(newarray, ouput_table)

