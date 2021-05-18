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
    in_features = r"D:\neartable\test\routes.shp"
    near_features = r"D:\neartable\test\routesD8.shp"
    out_table = r"D:\neartable\test\A_Btable.dbf"
    out_tableBA = r"D:\neartable\test\B_Atable.dbf"

    # Creating Near Table A-B and B-A
    arcpy.GenerateNearTable_analysis(in_features, near_features, out_table)
    #arcpy.GenerateNearTable_analysis(layerB, layerA, out_tableBA)


    # As ArcGis brings the FID (and not the RID) from the near_features in the process of near table, we must join and
    # arrange the fields.

    # Fixing A-B output
    # joinTable = r"D:\neartable\routesD8.dbf"
    # arcpy.JoinField_management(out_table, "NEAR_FID", joinTable, "OID")

    # arcpy.management.DeleteField(out_table, ["NEAR_FID", "NEAR_DIST"])

    # Fixing B-A output
    joinTable = r"D:\neartable\routesD8.dbf"
    # arcpy.JoinField_management(out_table2, "IN_FID", joinTable, "OID")
    # arcpy.management.DeleteField(out_table2, ["IN_FID", "NEAR_DIST"])
    # More fixing to have the same field names we have in out_table
    #arcpy.AddField_management(out_table2, "IN_FID", "LONG")
    # To copy the values, I did it manually because I do not find the right code to do it!!!
    # Delete the "old" near_fid field so both tables look the same
    #arcpy.management.DeleteField(out_table2, "NEAR_FID")

    # Intersection between the 2 line shapefiles

    # in_features = r"D:\EtcheminFullSet\routesD8.shp\routes.shp"
    # near_features = r"D:\EtcheminFullSet\routesD8.shp"
    # to_intersect = [in_features, near_features]
    # intersectOut = r"D:\neartable\intersection.shp"
    # arcpy.Intersect_analysis(to_intersect, intersectOut, "ALL", "", "POINT")

    # Counting the number of intersections

    # intersectOut = r"D:\neartable\intersect.shp"
    # arcpy.AddGeometryAttributes_management(intersectOut, "PART_COUNT")



    # We joint out_table and out_table2 (they have the same fields where RID is the routeD8 ID and IN_FID is the route ID).
   # merge_out = r"D:\neartable\merge_out.dbf"
    # arcpy.management.Merge([out_table, out_table2], merge_out)

    # Clean-up 1: deleting duplicate rows from merge_out
    # arcpy.DeleteIdentical_management(merge_out, ["IN_FID", "RID"])

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




    # Clean-up 2: assign to each pair the correspondent value of intersection and dismiss the pair with the smallest count.
    # Adding field COUNT to cleaned merge_out
    #arcpy.management.AddField(merge_out, "COUNT", "LONG")
    # merge_out = r"D:\neartable\merge_out.dbf"
    # intersect = r"D:\neartable\intersect_table.dbf"
    # Tried this but it did not work
    # q_table = r"D:\neartable\query_table.dbf"
    # where_clause = "merge_out.IN_FID = intersect_table.RouteID and merge_out.RID = intersect_table.RID"
    # arcpy.MakeQueryTable_management([merge_out, intersect], q_table, "USE_KEY_FIELDS", "merge_out.IN_FID", "", where_clause)

    # arcpy.management.AddField(merge_out, "ROUTE_D8", "TEXT")
    #
    # arcpy.management.AddField(intersect, "ROUTE_D8", "TEXT")
    # I would like to update the new field with the function [IN_FID]&" " &[RID]
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

