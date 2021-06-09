# -*- coding: utf-8 -*-

import arcpy
import os
def execute_AssignPointtoClosestPointOnRoute(points, points_RIDfield, points_onroute, points_onroute_RIDfield, output_shp, closest):

    """ This tool searches the closest point on a reach for each point with a route ID. It returns a shapefile with
    the points on route selected and the original data from the points layer"""

    # We need a shapefile points on route with the coordinates of each point
    # arcpy.AddXY_management(points_onroute)

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
        print(RID)
        i+=1
        arcpy.SelectLayerByAttribute_management("points_lyr", "NEW_SELECTION", points_RIDfield + " = "+ str(RID))
        arcpy.SelectLayerByAttribute_management("onroute_lyr", "NEW_SELECTION", points_onroute_RIDfield + " = "+ str(RID))
        table = arcpy.CreateScratchName("nt"+str(i), data_type="ArcInfoTable", workspace="in_memory")
        # For the each points and points on route with the same RID, we generate a near table that will keep only the closest
        # point on route to the original point.
        arcpy.GenerateNearTable_analysis("points_lyr", "onroute_lyr", table, closest=closest)
        list_tables.append(table)
    table = arcpy.CreateScratchName("nt" + str(i+1), data_type="ArcInfoTable", workspace="in_memory")
    arcpy.Merge_management(list_tables, table)

    arcpy.SelectLayerByAttribute_management("onroute_lyr", "CLEAR_SELECTION")
    arcpy.AddJoin_management("onroute_lyr", "FID", table, "NEAR_FID", "KEEP_COMMON")
    arcpy.AddJoin_management("onroute_lyr", os.path.basename(table)+".IN_FID", "points_lyr", "FID", "KEEP_COMMON")
    print([f.name for f in arcpy.ListFields("onroute_lyr")])
    arcpy.CopyFeatures_management("onroute_lyr", output_shp)

    fields_names = [f.name for f in arcpy.ListFields(output_shp)]
    onroute_fields_names = [f.name for f in arcpy.ListFields(points_onroute)]
    for i in range(2, len(onroute_fields_names)):
        print(output_shp)
        print(fields_names[i])
        print(onroute_fields_names[i])
        arcpy.AlterField_management(output_shp, fields_names[i], onroute_fields_names[i])
    index = i+1
    for i in range(index, index+4):
        arcpy.DeleteField_management(output_shp, fields_names[i])
    index += 4
    data_fields_names = [f.name for f in arcpy.ListFields(points)]
    for i in range(index, index+len(data_fields_names)):
        arcpy.AlterField_management(output_shp, fields_names[i], data_fields_names[i])

