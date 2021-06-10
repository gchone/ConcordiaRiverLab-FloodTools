# -*- coding: utf-8 -*-

import arcpy
import os
import numpy as np

def execute_AssignPointToClosestPointOnRoute(points, points_RIDfield, points_onroute, points_onroute_RIDfield, output_shp):

    """ This tool searches the closest point on a reach for each point with a route ID. It returns a shapefile with
    the points on route selected and the original data from the points layer"""



    # We need to select each time all the points with a certain RouteID and the points on route with the same RouteID and
    # save them as temporary layers.

    arcpy.MakeFeatureLayer_management(points, "points_lyr")
    arcpy.MakeFeatureLayer_management(points_onroute, "onroute_lyr")

    list_RIDs = []
    cursor = arcpy.da.SearchCursor(points, [points_RIDfield])
    for point in cursor:
        list_RIDs.append(point[0])
    list_RIDs = set(list_RIDs)

    list_tables = []
    i=0
    for RID in list_RIDs:
        i+=1
        arcpy.SelectLayerByAttribute_management("points_lyr", "NEW_SELECTION", points_RIDfield + " = "+ str(RID))
        arcpy.SelectLayerByAttribute_management("onroute_lyr", "NEW_SELECTION", points_onroute_RIDfield + " = "+ str(RID))
        table = arcpy.CreateScratchName("nt"+str(i), data_type="ArcInfoTable", workspace="in_memory")
        # For the each points and points on route with the same RID, we generate a near table that will keep only the closest
        # point on route to the original point.
        arcpy.GenerateNearTable_analysis("points_lyr", "onroute_lyr", table, closest="CLOSEST")
        list_tables.append(table)
    table = arcpy.CreateScratchName("nt" + str(i+1), data_type="ArcInfoTable", workspace="in_memory")
    arcpy.Merge_management(list_tables, table)

    # Join tables in order to have the data from the points linked with the points on route
    arcpy.SelectLayerByAttribute_management("onroute_lyr", "CLEAR_SELECTION")
    arcpy.AddJoin_management("onroute_lyr", "FID", table, "NEAR_FID", "KEEP_COMMON")
    arcpy.AddJoin_management("onroute_lyr", os.path.basename(table)+".IN_FID", "points_lyr", "FID", "KEEP_COMMON")

    # Exporting the resulting table into a shapefile creates unmanageable fields names.
    # We convert the table into a numpy array so we can rename the fields before exporting back to a shapefile
    total_fields_list = [str(f.name) for f in arcpy.ListFields("onroute_lyr")]
    onroute_fields_names = [str(f.name) for f in arcpy.ListFields(points_onroute)]
    fields_to_keep = total_fields_list[2:len(onroute_fields_names)]
    fields_to_keep.extend(total_fields_list[len(onroute_fields_names)+5:])
    fields_to_keep.remove(arcpy.Describe(points).basename+"."+points_RIDfield) # remove the second "RID"
    fields_to_keep.append("SHAPE@XY")

    nparray = arcpy.da.FeatureClassToNumPyArray("onroute_lyr", fields_to_keep)
    data_fields_names = [str(f.name) for f in arcpy.ListFields(points)]
    data_fields_names.remove(points_RIDfield) # remove the second "RID"
    wanted_fields_name = onroute_fields_names[2:]
    wanted_fields_name.extend(data_fields_names[2:])
    wanted_fields_name.append("XY")
    nparray.dtype.names = wanted_fields_name
    arcpy.da.NumPyArrayToFeatureClass(nparray, output_shp, "XY", spatial_reference=points_onroute)
