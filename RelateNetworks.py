# -*- coding: utf-8 -*-

# Author: Mariana
"""This tool creates a 'near table' to relate river routes('A') and D8/D4 routes ('B).
When it is run once, it omits some links and others in_features are linked to two different reaches from the near_feature layer.
For fixing this issue, the tool has to run twice (A to B and B to A). Then 2 clean-ups are required:
1. Clean up of duplicate combinations
2. Clean up wrong combination based on the number of intersections (points) between the two layers"""

# 1. Running Generate Near Table in both directions
import arcpy

def execute_RelateNetworks():
    # network_shapefile_A, network_shapefile_B, out_table
    # set workspace environment
    arcpy.env.workspace = r"D:\neartable\test"


    # Set required parameters for A-B.
    featuresA = r"D:\neartable\test\routes.shp"
    featuresB = r"D:\neartable\test\routesD8.shp"
    out_tableAB = r"D:\neartable\test\A_Btable.dbf"
    out_tableBA = r"D:\neartable\test\B_Atable.dbf"

    # Creating Near Table A-B and B-A
    arcpy.GenerateNearTable_analysis(featuresB, featuresA, out_tableBA)
    arcpy.GenerateNearTable_analysis(featuresA, featuresB, out_tableAB)


    """ As ArcGis brings the FID to the near table (and not the RID) from the featuresB in the process of creating the near table, 
    we must rearrange the fields in the table to create two tables with the same fields in order to be merged."""

    # Fixing out_tableAB
    arcpy.JoinField_management(out_tableAB, "NEAR_FID", featuresB, "FID")
    # Export table to save the join. I did it manually but I need to add this step
    out_tableABJoin = r"D\neartable\test\A_Btable_Join.dbf"
    arcpy.management.DeleteField(out_tableABJoin, ["NEAR_FID", "NEAR_DIST"])

    # Fixing out_tableBA
    arcpy.JoinField_management(out_tableBA, "IN_FID", featuresB, "FID")
    # Export table to save the join. I did it manually but I need to add this step
    out_tableBAJoin = r"D\neartable\test\B_Atable_Join.dbf"
    arcpy.management.DeleteField(out_tableBAJoin, ["IN_FID", "NEAR_DIST"])

    # More fixing is required to have the same field names we have in out_tableABJoin
    arcpy.AddField_management(out_tableBAJoin, "IN_FID", "LONG")
    # To copy the values, I did it manually because I do not find the right code to do it!!!
    # Delete the "old" near_fid field so both tables look the same
    arcpy.management.DeleteField(out_tableBAJoin, "NEAR_FID")

    # Merging the two tables to see all possible combinations
    merged_table = r"D\neartable\test\merged_table.dbf"
    arcpy.management.Merge([out_tableABJoin, out_tableBAJoin], merged_table)

    # Clean-up 1: deleting duplicate rows from merged_table
    arcpy.DeleteIdentical_management(merged_table, ["IN_FID", "RID"])

    # Clean-up 2: deleting rows based in the value of the points in the intersection of the two line layers.

    # Intersection between the two line shapefiles and counting the points of the intersection.
    featuresA = r"D:\neartable\test\routes.shp"
    featuresB = r"D:\neartable\test\routesD8.shp"
    to_intersect = [featuresA, featuresB]
    intersectOut = r"D:\neartable\test\intersection.shp"
    arcpy.Intersect_analysis(to_intersect, intersectOut, "ALL", "", "POINT")
    arcpy.AddGeometryAttributes_management(intersectOut, "PART_COUNT")

    # To do the clean-up according the amount of points for each intersection with the merged_table (already cleaned for duplicates),
    # we create and auxiliary field ("ROUTE_D8") with the IN_FID and RID values).

    arcpy.management.AddField(merged_table, "ROUTE_D8", "TEXT")
    arcpy.management.AddField(intersectOut, "ROUTE_D8", "TEXT")

    # These fields are calculated using the expression [IN_FID]&" "& [RID] for merged_table; and [RouteID]&" "& [RID] for intersectOut.




    # cursor_neartable = arcpy.da.SearchCursor(merge_out, ["OID@", "IN_FID", "RID", "PART_COUNT"])
    # rowsOID_to_delete = []
    # part_count_dict_A = {}
    # part_count_dict_B = {}
    # for row in cursor_neartable:
    #     if part_count_dict_A.has_key(row[2]):
    #         if row[3] < part_count_dict_A[row[2]][3]:
    #             rowsOID_to_delete.append(row[0])
    #         else:
    #             rowsOID_to_delete.append(part_count_dict_A[row[2]][0])
    #             part_count_dict_A[row[2]] = row
    #     else:
    #        part_count_dict_A[row[2]] = row
    #
    #     if part_count_dict_B.has_key(row[1]):
    #         if row[3] < part_count_dict_B[row[1]][3]:
    #             rowsOID_to_delete.append(row[0])
    #         else:
    #             rowsOID_to_delete.append(part_count_dict_B[row[1]][0])
    #             part_count_dict_B[row[1]] = row
    #     else:
    #        part_count_dict_B[row[1]] = row
    #
    # cursor_neartable = arcpy.da.UpdateCursor(merge_out, ["OID@"])
    # for row in cursor_neartable:
    #     if row[0] in rowsOID_to_delete:
    #         cursor_neartable.deleteRow()
    #





    # arcpy.JoinField_management(merge_out, "ROUTE_D8", intersect, "ROUTE_D8")
    # cursor_neartable = arcpy.da.UpdateCursor(merge_out, ["PART_COUNT"])
    # for row in cursor_neartable:
    #         if row[0] < 3:
    #             cursor_neartable.deleteRow()

    # point_feature = r"D:\EtcheminFullSet\D8points_toproject.shp"
    # line_routes =  r"D:\TestLinearRef\routes_proj.shp"
    # out_table3 = r"D:\TestLinearRef\d8points_route_check3.dbf"
    # tol = "500 Meters"
    # props = "RID POINT meas"
    #
    # arcpy.lr.LocateFeaturesAlongRoutes(point_feature, line_routes, "RouteID", tol, out_table3, props, "FIRST", "DISTANCE", "ZERO", "FIELDS", "M_DIRECTON")

    # This is useful but not completely OK as the real process should be that if there are two combinations that have one
    # element in common, the one with the lowest value should be eliminated. So, this process needs this adjustment

    return

    if __name__ == "__main__":
        execute_RelateNetworks()

