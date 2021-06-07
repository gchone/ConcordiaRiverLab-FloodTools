# -*- coding: utf-8 -*-

import arcpy
def execute_LocatePointsAlongRoutes(points, routes, output, distance):

    """ To Locate Features Along Routes, we want the point to be located following the Near Table relationship in the reach
    (RouteID) indicated in the table. D8points.shp has all the points generated within routesD8.shp. Each time all the
    points with a certain RouteID from the  point layer and a reach (with the same RouteID) are selected to execute the
     Locate Points Along Routes. The output is  a table with the linear referencing of all the points to be projected
     on the route network."""

    # We need to select each time all the points with a certain RouteID and project them in the same RouteID.

    # The point and routes shapefiles (or feature classes within a GDB) are saved as temporary layers.

    arcpy.MakeFeatureLayer_management(points, "pts_layer")
    arcpy.MakeFeatureLayer_management(routes, "route_layer")


    cursor = arcpy.da.SearchCursor(routes, ["RID"])
    list_tables = []
    i=0
    for reach in cursor:
        i+=1
        arcpy.SelectLayerByAttribute_management("pts_layer", "NEW_SELECTION", "RID = "+str(reach[0]))
        arcpy.SelectLayerByAttribute_management("route_layer", "NEW_SELECTION", "RID = " + str(reach[0]))
        table = arcpy.CreateScratchName("net"+str(i), data_type="ArcInfoTable", workspace="in_memory")
        arcpy.lr.LocateFeaturesAlongRoutes("pts_layer", "route_layer", "RID", distance, table, "RID POINT MEAS")
        list_tables.append(table)

    arcpy.Merge_management(list_tables, output)






