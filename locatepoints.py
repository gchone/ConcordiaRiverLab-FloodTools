# -*- coding: utf-8 -*-

def execute_LocatePointsAlongRoutes ()
""" To Locate Features Along Routes, we want the point to be located following the Near Table relationship in the reach 
(RouteID) indicated in the table. D8points.shp has all the points generated within routesD8.shp. Each time all the 
points with a certain RouteID from the  point layer and a reach (with the same RouteID) are selected to execute the
 Locate Points Along Routes. The output is  a table with the linear referencing of all the points to be projected 
 on the route network."""

# We need to select each time all the points with a certain RouteID and project them in the same RouteID.

import arcpy
import ArcpyGarbageCollector as gc

arcpy.env.workspace = r"D:\TestLinearRef"
# arcpy.env.workspace = r"D:\neartable\test"
in_features = r"D:\TestLinearRef\DataToProject_ML.shp"
routes = r"D:\TestLinearRef\riversroute.shp"
output = r"D:\TestLinearRef\mergetable.dbf"
distance_param = 100

# The point and routes shapefiles (or feature classes within a GDB) are saved as temporary layers.
arcpy.MakeFeatureLayer_management(in_features, "pts_layer")
arcpy.MakeFeatureLayer_management(routes, "route_layer")

cursor = arcpy.da.SearchCursor(routes, ["RID"])
list_tables = []
try:
    for reach in cursor:
        arcpy.SelectLayerByAttribute_management("pts_layer", "NEW_SELECTION", "RID = "+str(reach[0]))
        arcpy.SelectLayerByAttribute_management("route_layer", "NEW_SELECTION", "RID = " + str(reach[0]))
        table = arcpy.CreateScratchName("net", data_type="ArcInfoTable", workspace=arcpy.env.scratchWorkspace)
        gc.AddToGarbageBin(table)
        arcpy.LocateFeaturesAlongRoutes_lr("pts_layer", "route_layer", "RID", distance_param, table)
        list_tables.append(table)

    arcpy.Merge_management(list_tables, output)

finally:
    gc.CleanTempFiles()





# Select the point with a certain RouteID from point layer (D8pts). This layer has been previously joined to the near table.
# Select the line with the same Route ID from the Routes layer
#pointLayer = r"D:\neartable\test\D8pts.shp"
#fields = ["RouteID"]
#qry = "RouteID = 0"


# Run locate points along route tool
# Repeat the process for all the reaches




# #in_features = r"D:\neartable\test\D8points_tolocate.shp"
# #out_layer = r"D:\neartable\test\location.gdb\points_lyr"
# arcpy.env.overwriteOutput = True
# try:
#     #Make a layer from a feature class
#     arcpy.MakeFeatureLayer_management("D8pts.shp", "points_lyr")
#
#     #Make a selection for a RouteID
#     arcpy.SelectLayerByAttribute_management("points_lyr", "NEW_SELECTION", "RouteID = 0"
#
#     #Write the new selected features to anew featureclass
#     out_features = r"D:\neartable\test\location.gdb\pointsR0"
#     arcpy.CopyFeatures_management(in_features, out_features)
#
# except:
#    print(arcpy.GetMessages())