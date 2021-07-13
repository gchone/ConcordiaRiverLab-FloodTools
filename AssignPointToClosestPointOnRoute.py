# -*- coding: utf-8 -*-

import arcpy
import os
import numpy as np
import ArcpyGarbageCollector as gc

def execute_AssignPointToClosestPointOnRoute(points, points_RIDfield, list_fields_to_keep, routes, routes_IDfield, points_onroute, points_onroute_RIDfield, points_onroute_distfield, output_table, stat="MEAN"):

    """ This tool searches the closest point on a reach for each point with a route ID. It returns a shapefile with
    the points on route selected and the original data from the points layer"""

    # We need to select each time all the points with a certain RouteID and the points on route with the same RouteID and
    # save them as temporary layers.

    arcpy.MakeFeatureLayer_management(points, "points_lyr")
    # Layer for the points on route: made by Make Route Event Layer to use the linear referencing
    arcpy.MakeRouteEventLayer_lr(routes, routes_IDfield, points_onroute,
                                 points_onroute_RIDfield+" POINT "+points_onroute_distfield, "onroute_lyr")

    list_RIDs = []
    cursor = arcpy.da.SearchCursor(points, [points_RIDfield])
    for point in cursor:
        list_RIDs.append(point[0])
    list_RIDs = set(list_RIDs)

    if stat == "MEAN":
        list_tables = []
        for RID in list_RIDs:
            arcpy.SelectLayerByAttribute_management("points_lyr", "NEW_SELECTION", points_RIDfield + " = " + str(RID))
            arcpy.SelectLayerByAttribute_management("onroute_lyr", "NEW_SELECTION", points_onroute_RIDfield + " = " + str(RID))
            table = gc.CreateScratchName("nt", data_type="ArcInfoTable", workspace="in_memory")
            # For the each points and points on route with the same RID, we generate a near table that will keep only the closest
            # point on route to the original point.
            arcpy.GenerateNearTable_analysis("points_lyr", "onroute_lyr", table, closest="CLOSEST")
            list_tables.append(table)
        table = gc.CreateScratchName("nt", data_type="ArcInfoTable", workspace="in_memory")
        arcpy.Merge_management(list_tables, table)
        arcpy.SelectLayerByAttribute_management("points_lyr", "CLEAR_SELECTION")
        arcpy.SelectLayerByAttribute_management("onroute_lyr", "CLEAR_SELECTION")

        # Join tables in order to have the data from the points linked with the points on route
        onroute_lyr_IDfield = arcpy.Describe("onroute_lyr").OIDFieldName
        points_lyr_IDfield = arcpy.Describe("points_lyr").OIDFieldName

        arcpy.AddJoin_management("points_lyr", points_lyr_IDfield, table, "IN_FID", "KEEP_COMMON")
        arcpy.AddJoin_management("points_lyr", os.path.basename(table) + ".NEAR_FID", "onroute_lyr", onroute_lyr_IDfield,
                                 "KEEP_COMMON")

        total_fields_list = [str(f.name) for f in arcpy.ListFields("points_lyr")]
        onroute_fields_names = [str(f.name) for f in arcpy.ListFields("onroute_lyr")]
        data_fields_names = [str(f.name) for f in arcpy.ListFields(points)]
        fields_to_keep = total_fields_list[len(data_fields_names)+5:]
        for field in list_fields_to_keep:
            fields_to_keep.append(arcpy.Describe(points).basename + "." + field)

        nparray = arcpy.da.FeatureClassToNumPyArray("points_lyr", fields_to_keep)

        # rename fields
        wanted_fields_name = onroute_fields_names[1:-1]
        for field in list_fields_to_keep:
            wanted_fields_name.append(field)
        nparray.dtype.names = wanted_fields_name


        # compute values for the same main channel points -> average
        idfield = nparray.dtype.names[0]
        means_ids = np.unique(nparray[[idfield]])
        means = np.empty(means_ids.shape[0], dtype=nparray.dtype)
        i = 0
        for id in means_ids:
            tmp_all = nparray[np.where(nparray[[idfield]] == id)]
            means[i] = nparray[np.where(nparray[[idfield]] == id)][0]
            for field in list_fields_to_keep:
                means[field][i] = np.mean(tmp_all[field])
            i+=1

        arcpy.da.NumPyArrayToTable(means, output_table)

    else:
        # stat == "CLOSEST"
        # In the case we only need the data from the closest point, the join needs to be done in reverse
        #  (joining the onroute points with the data points instead of the data points with the onroute points)

        list_tables = []
        for RID in list_RIDs:
            arcpy.SelectLayerByAttribute_management("points_lyr", "NEW_SELECTION", points_RIDfield + " = "+ str(RID))
            arcpy.SelectLayerByAttribute_management("onroute_lyr", "NEW_SELECTION", points_onroute_RIDfield + " = "+ str(RID))
            table = gc.CreateScratchName("nt", data_type="ArcInfoTable", workspace="in_memory")
            # For the each points and points on route with the same RID, we generate a near table that will keep only the closest
            # data point to the point on route.
            arcpy.GenerateNearTable_analysis("onroute_lyr", "points_lyr", table, closest="CLOSEST")
            list_tables.append(table)
        table = gc.CreateScratchName("nt", data_type="ArcInfoTable", workspace="in_memory")
        arcpy.Merge_management(list_tables, table)
        arcpy.SelectLayerByAttribute_management("points_lyr", "CLEAR_SELECTION")
        arcpy.SelectLayerByAttribute_management("onroute_lyr", "CLEAR_SELECTION")

        # Join tables in order to have the data from the points on route linked with the data points
        onroute_lyr_IDfield = arcpy.Describe("onroute_lyr").OIDFieldName
        points_lyr_IDfield = arcpy.Describe("points_lyr").OIDFieldName

        arcpy.AddJoin_management("onroute_lyr", onroute_lyr_IDfield, table, "IN_FID", "KEEP_COMMON")
        arcpy.AddJoin_management("onroute_lyr", os.path.basename(table) + ".NEAR_FID", "points_lyr",
                                 points_lyr_IDfield,
                                 "KEEP_COMMON")

        total_fields_list = [str(f.name) for f in arcpy.ListFields("onroute_lyr")]
        onroute_fields_names = [str(f.name) for f in arcpy.ListFields(points_onroute)]
        data_fields_names = [str(f.name) for f in arcpy.ListFields("points_lyr")]
        fields_to_keep = total_fields_list[1:len(onroute_fields_names)]

        for field in list_fields_to_keep:
            fields_to_keep.append(arcpy.Describe(points).basename + "." + field)

        nparray = arcpy.da.FeatureClassToNumPyArray("onroute_lyr", fields_to_keep)

        # rename fields
        wanted_fields_name = onroute_fields_names[1:]
        for field in list_fields_to_keep:
            wanted_fields_name.append(field)

        nparray.dtype.names = wanted_fields_name

        arcpy.da.NumPyArrayToTable(nparray, output_table)

