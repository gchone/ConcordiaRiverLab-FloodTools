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
import os.path

import arcpy


def execute_RelateNetworks(shapefile_A, RID_A, shapefile_B, RID_B, out_table, messages):

    # Compare if both featura class have the same amount of rows
    try:
        comp_tables = arcpy.FeatureCompare_management (shapefile_A, shapefile_B, "FID", compare_type="ATTRIBUTES_ONLY", continue_compare= "CONTINUE_COMPARE", out_compare_file="COMP")
        print (comp_tables.getOutput(1))
        print(arcpy.GetMessages())

    except Exception as err:
        print(err.args[0])


    # Execute Near Table creation A-B and B-A
    tempAB = arcpy.CreateScratchName("tempAB", data_type = "ArcInfoTable", workspace="in_memory")
    arcpy.GenerateNearTable_analysis(shapefile_A, shapefile_B, tempAB)

    tempBA = arcpy.CreateScratchName("tempBA", data_type = "ArcInfoTable", workspace="in_memory")
    arcpy.GenerateNearTable_analysis(shapefile_B, shapefile_A, tempBA)

    # Merging the two tables to see all possible combinations. This step requires setting Field Map objects to Field
    # mapping objects. This step allows to customize the output table of the merge.

    fldMap_A_OID = arcpy.FieldMap()
    fldMap_B_OID = arcpy.FieldMap()
    fieldMappings = arcpy.FieldMappings()

    tempabA = "IN_FID"
    tempbaA = "NEAR_FID"

    tempabB = "NEAR_FID"
    tempbaB = "IN_FID"

    fldMap_A_OID.addInputField(tempAB, tempabA)
    fldMap_A_OID.addInputField(tempBA, tempbaA)

    fldMap_B_OID.addInputField(tempAB, tempabB)
    fldMap_B_OID.addInputField(tempBA, tempbaB)

    # Output field properties

    outfieldA = fldMap_A_OID.outputField
    outfieldA.name = "A_OID"
    fldMap_A_OID.outputField = outfieldA

    outfieldB = fldMap_B_OID.outputField
    outfieldB.name = "B_OID"
    fldMap_B_OID.outputField = outfieldB

    #Add the FieldMap objects to the FieldMappings object
    fieldMappings.addFieldMap(fldMap_A_OID)
    fieldMappings.addFieldMap(fldMap_B_OID)

    # Merge the two feature classes
    #temp_merged = arcpy.CreateScratchName("merge", data_type = "ArcInfoTable", workspace="in_memory")
    arcpy.Merge_management([tempAB, tempBA], out_table, fieldMappings)
    #if arcpy.Describe(arcpy.env.scratchWorkspace).dataType == "Folder":
    #    # when working in a folder, the merge result is a dbf file
    #    temp_merged = temp_merged+".dbf"
    #gc.AddToGarbageBin(temp_merged)

    # Clean-up 1: deleting duplicate rows from merged_table
    arcpy.DeleteIdentical_management(out_table, ["A_OID", "B_OID"])

    # Intersection between the two line shapefiles and counting the points of the intersection.
    to_intersect = [shapefile_A, shapefile_B]

    temp_intersect = arcpy.CreateScratchName("temp", data_type="FeatureClass", workspace="in_memory")


    arcpy.Intersect_analysis(to_intersect, temp_intersect, "ONLY_FID", "", "POINT")
    # "PART_COUNT" provides de amount of points in each intersection between the two line shapefiles. Analyzing this
    # value allows to choose the correct combination in the near_table (temp_merged). If we have a combination like
    # 5-8 with a part_count=1 (being the 5 the # routeID and 8 the RID) and 5-10 with a part_count = 256, the last
    # combination is the correct one.
    arcpy.AddGeometryAttributes_management(temp_intersect, "PART_COUNT")

    arcpy.management.AddField(out_table, "MERGED_OID", "TEXT", 20)
    arcpy.management.AddField(temp_intersect, "MERGED_OID", "TEXT", 20)

    arcpy.CalculateField_management(out_table, "MERGED_OID", "'!A_OID!_!B_OID!'", "PYTHON_9.3")

    name_fieldA = arcpy.ListFields(temp_intersect)[2].name
    name_fieldB = arcpy.ListFields(temp_intersect)[3].name

    arcpy.CalculateField_management(temp_intersect, "MERGED_OID", "'!"+name_fieldA+"!_!"+name_fieldB+"!'", "PYTHON_9.3")

    # Joining both tables
    arcpy.JoinField_management(out_table, "MERGED_OID", temp_intersect, "MERGED_OID")


    # Combinations with PART_COUNT close to 1 should be deleted.
    cursor_neartable = arcpy.da.UpdateCursor(out_table, ["PART_COUNT"])
    for row in cursor_neartable:
        if row[0] < 2:
            cursor_neartable.deleteRow()

    # Join RIDs
    arcpy.JoinField_management(out_table, "A_OID", shapefile_A, arcpy.Describe(shapefile_A).OIDFieldName, RID_A)
    arcpy.JoinField_management(out_table, "B_OID", shapefile_B,  arcpy.Describe(shapefile_B).OIDFieldName, RID_B)
    todelete = []
    for field in arcpy.ListFields(out_table)[1:-2]:
        todelete.append(field.name)
    todelete.remove("PART_COUNT")

    # Clean-up extra fields
    arcpy.DeleteField_management(out_table, todelete)

    # Copy the result
    #arcpy.Copy_management(temp_merged, out_table)

   #
   # # This option can be problematic when 2 reaches in one layer are liked to one reach in the other but both are correct and have large values of PART_COUNTS
   #
   #  cursor_neartable = arcpy.da.SearchCursor(temp_merged, ["OID@", "IN_FID", "RID", "PART_COUNT"])
   #  rowsOID_to_delete = []
   #  part_count_dict_A = {}
   #  part_count_dict_B = {}
   #  for row in cursor_neartable:ab
   #      if part_count_dict_A.has_key(row[2]):bb
   #          if row[3] < part_count_dict_A[row[2]][3]:
   #              rowsOID_to_delete.append(row[0])
   #          else:
   #              rowsOID_to_delete.append(part_count_dict_A[row[2]][0])
   #              part_count_dict_A[row[2]] = row
   #      else:
   #         part_count_dict_A[row[2]] = row
   #
   #      if part_count_dict_B.has_key(row[1]):
   #          if row[3] < part_count_dict_B[row[1]][3]:
   #              rowsOID_to_delete.append(row[0])
   #          else:
   #              rowsOID_to_delete.append(part_count_dict_B[row[1]][0])
   #              part_count_dict_B[row[1]] = row
   #      else:
   #         part_count_dict_B[row[1]] = row
   #
   #  cursor_neartable = arcpy.da.UpdateCursor(temp_merged, ["OID@"])
   #  for row in cursor_neartable:
   #      if row[0] in rowsOID_to_delete:
   #          cursor_neartable.deleteRow()





