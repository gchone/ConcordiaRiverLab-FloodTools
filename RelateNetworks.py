# -*- coding: utf-8 -*-

# Author: Mariana
"""This tool creates a 'near table' to relate river routes('A') and D8/D4 routes ('B').
When it runs once, some links are omitted and others in_features are linked to two different reaches from the near_feature layer.
This issue is related to the way ArcGis calculates distance in proximity tools such as "Near Table"
- Multiple features may be equally closest to another feature. When this occurs, one of the equally closest features is randomly selected as the closest.
- The distance between two features is zero whenever there is at least one x,y coordinate that is shared between them.
- This means that when two features intersect, overlap, cross, or touch, the distance between them is zero.
For fixing this issue, the tool has to run twice (A to B and B to A). Then 2 clean-ups are required:
1. Clean up of duplicate combinations
2. Clean up wrong combination based on the number of intersections (points) between the two layers"""

# 1. Running Generate Near Table in both directions
import arcpy
import ArcpyGarbageCollector as gc

def execute_RelateNetworks():
    # shapefile_A, shapefile_B, out_table

    # set workspace environment
    arcpy.env.workspace = r"D:\TestLinearRef\neartabletool_example"

try:
    # Set required parameters for A-B.
    shapefile_A = r"D:\TestLinearRef\neartabletool_example\riversroute.shp"
    shapefile_B = r"D:\TestLinearRef\neartabletool_example\D8routes.shp"
    out_table = r"D:\TestLinearRef\neartabletool_example\neartable.dbf"


    tempAB = arcpy.CreateScratchName("temp", data_type = "ArcInfoTable", workspace=arcpy.env.scratchWorkspace)
    tempBA = arcpy.CreateScratchName("temp", data_type = "ArcInfoTable", workspace=arcpy.env.scratchWorkspace)
    gc.AddToGarbageBin(tempBA, tempAB)

    # Execute Near Table creation A-B and B-A
    arcpy.GenerateNearTable_analysis(shapefile_B, shapefile_A, tempBA)
    arcpy.GenerateNearTable_analysis(shapefile_A, shapefile_B, tempAB)


# As ArcGis brings the FID to the near table (and not the RID) from the layer B in the process of creating the near table,
# we must rearrange the fields in the table to create two tables with the same fields in order to be merged.

    # Fixing tempAB
    arcpy.JoinField_management(tempAB, "NEAR_FID", shapefile_B, "FID")
    # Export table to save the join. I did it manually but I need to add this step
    #out_tableABJoin = r"D:\TestLinearRef\neartabletool_example\A_Btable_Join.dbf"
    arcpy.management.DeleteField(tempAB, ["NEAR_FID", "NEAR_DIST"])

    # Fixing tempBA
    arcpy.JoinField_management(tempBA, "IN_FID", shapefile_B, "FID")
    # Export table to save the join. I did it manually but I need to add this step
    # out_tableBAJoin = r"D:\TestLinearRef\neartabletool_example\B_Atable_Join.dbf"
    arcpy.management.DeleteField(tempBA, ["IN_FID", "NEAR_DIST"])

    # More fixing is required in tempBA to have the same field names we have in tempAB. The "IN_FID" field has to take the
    #values from the "NEAR_FID" field.
    arcpy.AddField_management(tempBA, "IN_FID", "LONG")
    for x in tempBA
        if x.name == "IN_FID"
            tempBA.append ("NEAR_FID")

        # Delete the "old" near_fid field so both tables look the same
    arcpy.management.DeleteField(tempBA, "NEAR_FID")

    # Merging the two tables to see all possible combinations
    temp_merged = arcpy.CreateScratchName("temp", data_type = "ArcInfoTable", workspace=arcpy.env.scratchWorkspace)
    arcpy.management.Merge([tempAB, tempBA], temp_merged)
    gc.AddToGarbageBin(temp_merged)

    # Clean-up 1: deleting duplicate rows from merged_table
    arcpy.DeleteIdentical_management(temp_merged, ["IN_FID", "RID"])

    # Clean-up 2: deleting rows based in the count of the points in the intersection of the two line layers.

    # Intersection between the two line shapefiles and counting the points of the intersection.
    to_intersect = [shapefile_A, shapefile_B]
    temp_intersect = arcpy.CreateScratchName("temp", data_type = "Shapefile", workspace=arcpy.env.scratchWorkspace)
    gc.AddToGarbageBin(temp_intersect)

    arcpy.Intersect_analysis(to_intersect, temp_intersect, "ALL", "", "POINT")
    # "PART_COUNT" provides de amount of points in each intersection between the two line shapefiles. Analyzing this value
    # allows as to choose the correct combination in the near_table (temp_merged). If we have a combination like 5-8 with a part_count=1 (being the 5 the
    # routeID and 8 the RID) and 5-10 with a part_count = 256, the last combination is the correct one.
    arcpy.AddGeometryAttributes_management(temp_intersect, "PART_COUNT")

    # To do the clean-up according the amount of points for each intersection with the merged_table (already cleaned for duplicates),
    # we create and auxiliary field ("ROUTE_D8") with the IN_FID and RID values to be able to joint the intersection table with the merged_table.

    arcpy.management.AddField(temp_merged, "ROUTE_D8", "TEXT")
    arcpy.management.AddField(temp_intersect, "ROUTE_D8", "TEXT")

    # These fields are calculated using the expression [IN_FID]&" "& [RID] for merged_table; and [RouteID]&" "& [RID] for intersectOut (Need to add this line).
    temp_merged_fixed = temp_merged.replace("ROUTE_D8", {}:{}".format(!IN_FID!, !RID!))
    temp_intersect_fixed = tempr_intersect.replace("ROUTE_D8", {}:{}".format(!Route_ID!, !RID!)

    # Joining both tables
    arcpy.JoinField_management(temp_merged, "ROUTE_D8", temp_intersect, "ROUTE_D8")

    # Combinations with PART_COUNT close to 1 should be deleted.
    cursor_neartable = arcpy.da.UpdateCursor(temp_merged, ["PART_COUNT"])
    for row in cursor_neartable:
            if row[0] < 3:
                cursor_neartable.deleteRow()

   # This option can be problematic when 2 reaches in one layer are liked to one reach in the other but both are correct and have large values of PART_COUNTS

    cursor_neartable = arcpy.da.SearchCursor(temp_merged, ["OID@", "IN_FID", "RID", "PART_COUNT"])
    rowsOID_to_delete = []
    part_count_dict_A = {}
    part_count_dict_B = {}
    for row in cursor_neartable:
        if part_count_dict_A.has_key(row[2]):
            if row[3] < part_count_dict_A[row[2]][3]:
                rowsOID_to_delete.append(row[0])
            else:
                rowsOID_to_delete.append(part_count_dict_A[row[2]][0])
                part_count_dict_A[row[2]] = row
        else:
           part_count_dict_A[row[2]] = row

        if part_count_dict_B.has_key(row[1]):
            if row[3] < part_count_dict_B[row[1]][3]:
                rowsOID_to_delete.append(row[0])
            else:
                rowsOID_to_delete.append(part_count_dict_B[row[1]][0])
                part_count_dict_B[row[1]] = row
        else:
           part_count_dict_B[row[1]] = row

    cursor_neartable = arcpy.da.UpdateCursor(temp_merged, ["OID@"])
    for row in cursor_neartable:
        if row[0] in rowsOID_to_delete:
            cursor_neartable.deleteRow()


# Finally the cleaned table is saved as neartable.dbf
finally:
    out_table = r"D:\TestLinearRef\neartabletool_example\neartable.dbf"
    arcpy.Copy.management(temp_merged, out_table)

gc.CleanTempFiles()
if __name__ == "__main__":


