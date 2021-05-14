# -*- coding: utf-8 -*-
import arcpy.analysis

import tree.RiverNetwork
from BedAssessmentDirectLinearNet import *
from Simple1Dhydraulic import *
from datetime import datetime
import ArcpyGarbageCollector as gc


class Messages():
    def addErrorMessage(self, text):
        print (text)

    def addWarningMessage(self, text):
        print (text)

    def addMessage(self, text):
        print(text)


def test_basic_network():
    # test modif

    route = r"E:\InfoCrue\Refontebathy\TestLinearRef.gdb\routeflowdir"
    routelinks = r"E:\InfoCrue\Refontebathy\TestLinearRef.gdb\routeflowdir_links"
    points1 = r"E:\InfoCrue\Refontebathy\TestLinearRef.gdb\data05_22"
    createtable = r"E:\InfoCrue\Refontebathy\TestLinearRef.gdb\newtable4"

    # Lecture des données 1 - on construit le réseau de rivière à partir des routes (shapefiles de lignes avec référencement linéaire)
    dict_attr_field = {"id": "RouteID",
                       "length": "SHAPE@LENGTH",
                       }
    rivernet = tree.RiverNetwork.RiverNetwork(route, routelinks, dict_attr_field)

    # Lecture des données 2 - on ajoute les informations des points (avec leur référencement linéaire)
    dict_attr_field = {"id": "PointID",
                       "reach_id": "RouteID",
                       "dist": "MEAS",
                       "offset": "DISTANCE",
                       "wslidar": "ws",
                       "Q": "Q",
                       "width": "width"
                       }
    dict_attr_field = {"id": "OID@",
                       "reach_id": "RID",
                       "dist": "MEAS",
                       "offset": "DISTANCE",
                       "width": "width",
                       }
    rivernet.add_points_collection("chemin d'un shapefile de points", dict_attr_field, "width")
    dict_attr_field = {"id": "OID@",
                       "reach_id": "RID",
                       "dist": "MEAS",
                       "offset": "DISTANCE",
                       "discharge": "Q",
                       }
    rivernet.add_points_collection("chemin d'un shapefile de points", dict_attr_field, "discharge")
    dict_attr_field = {"id": "OID@",
                       "reach_id": "RID",
                       "dist": "MEAS",
                       "offset": "DISTANCE",
                       }
    rivernet.add_points_collection("chemin d'un shapefile de points", dict_attr_field, "d4")

    # Traitement
    # Spatialisation des données (elevation de la surface de l'eau, largeur, débit) au points souhaitées
    # On crée les attributs "z", "width", "Q" pour chaque point dans la collection de points "d4"
    # Exemple de parcour de points:

    for reach in rivernet.browse_reaches():
        for point in reach.browse_points(points_collection="water_surface"):
            point.z2 = point.z - 100


def test_bed_assess():
    route = r"E:\InfoCrue\Refontebathy\SyntheticInputs\route.shp"
    routelinks = r"E:\InfoCrue\Refontebathy\SyntheticInputs\routelinks.dbf"

    points1 = r"E:\InfoCrue\Refontebathy\SyntheticInputs\memorytest\data13.dbf"
    # createtable = r"E:\InfoCrue\Refontebathy\SyntheticInputs\basicsolver_auto.dbf"
    createtable = r"E:\InfoCrue\Refontebathy\SyntheticInputs\memorytest\solverdata13.dbf"

    print ("start: " + str(datetime.now()))
    # Lecture des données 1 - on construit le réseau de rivière à partir des routes (shapefiles de lignes avec référencement linéaire)
    dict_attr_field = {"id": "Id",
                       "length": "SHAPE@LENGTH",
                       }
    rivernet = tree.RiverNetwork.RiverNetwork(route, routelinks, dict_attr_field)

    # Lecture des données 2 - on ajoute les informations des points (avec leur référencement linéaire)
    dict_attr_field = {"id": "id",
                       "reach_id": "RID",
                       "dist": "dist2",
                       "offset": "offset",
                       "wslidar": "ws",
                       "Q": "q",
                       "width": "w"
                       }
    rivernet.add_points_collection(points1, dict_attr_field, "data")

    print ("loaded: " + str(datetime.now()))

    execute_BedAssessment(rivernet, "data", 0.03, 0.0001, messages)
    print("bed done: " + str(datetime.now()))

    # Enregistrement des données dans une nouvelle table
    dict_attr_field = {"id": ("ORIG_ID", "LONG"),
                       "dist": ("MEAS", "FLOAT"),
                       "z": ("bed_elev", "FLOAT"),
                       "v": ("v", "FLOAT"),
                       "h": ("h", "FLOAT"),
                       "Fr": ("Fr", "FLOAT"),
                       "s": ("S", "FLOAT"),
                       "solver": ("solver", "TEXT", 20)
                       }

    rivernet.save_points(createtable, dict_attr_field, "data")

    print ("saved: " + str(datetime.now()))


def test_1Dhydro():
    route = r"E:\InfoCrue\Refontebathy\SyntheticInputs\route.shp"
    routelinks = r"E:\InfoCrue\Refontebathy\SyntheticInputs\routelinks.dbf"

    points1 = r"E:\InfoCrue\Refontebathy\SyntheticInputs\basicsolver_auto.dbf"
    createtable = r"E:\InfoCrue\Refontebathy\SyntheticInputs\verif_basicsolver_auto.dbf"

    dict_attr_field = {"id": "Id",
                       "length": "SHAPE@LENGTH",
                       }
    rivernet = tree.RiverNetwork.RiverNetwork(route, routelinks, dict_attr_field)

    dict_attr_field = {"id": "ORIG_ID",
                       "reach_id": "RID",
                       "dist": "MEAS",
                       "offset": "offset",
                       "z": "bed_elev",
                       "Q": "Q",
                       "width": "width"
                       }
    rivernet.add_points_collection(points1, dict_attr_field, "data")

    execute_Simple1Dhydraulic(rivernet, "data", 0.03, 0.01, messages)

    # Enregistrement des données dans une nouvelle table
    dict_attr_field = {"id": ("ORIG_ID", "LONG"),
                       "dist": ("MEAS", "FLOAT"),
                       "ws": ("ws", "FLOAT"),
                       }

    rivernet.save_points(createtable, dict_attr_field, "data")


def test_treecreate():
    # rivernet = r"D:\TestLinearRef\rivers.shp"
    # route_shapefile = r"D:\TestLinearRef\riversroute.shp"
    # routelinks_table = r"D:\TestLinearRef\riversroute_links.dbf"
    # routeID_field = "RID"
    # downstream_reach_field = "DownEnd"

    # execute_CreateTreeFromShapefile(rivernet, route_shapefile, routelinks_table, routeID_field, downstream_reach_field)

    r_flowdir = arcpy.Raster(r"D:\TestLinearRef\lidar10m_fd")
    str_frompoints = r"D:\TestLinearRef\FromPoints.shp"
    route_shapefile = r"D:\TestLinearRef\riversroute_fd.shp"
    routelinks_table = r"D:\TestLinearRef\riversroute_links_fd.dbf"
    str_output_points = r"D:\TestLinearRef\points_along_fd.dbf"
    routeID_field = "RID"

    execute_TreeFromFlowDir(r_flowdir, str_frompoints, route_shapefile, routelinks_table, routeID_field,
                            str_output_points, messages)


def test_cursor():
    # table = r"D:\TestLinearRef\ml_all_plus3.dbf"
    # outputtable = r"D:\TestLinearRef\ml_all_plus3_filtered.dbf"
    #
    # try:
    #     newtablepath = os.path.join(arcpy.env.scratchWorkspace, "copytable.dbf")
    #     arcpy.Copy_management(table, newtablepath)
    #     gc.AddToGarbageBin(newtablepath)
    #
    #     cursor = arcpy.da.UpdateCursor(newtablepath, ["newRID", "RID"])
    #     for row in cursor:
    #         if row[0] != row[1]:
    #             cursor.deleteRow()
    #
    #     route_shapefile = r"D:\TestLinearRef\riversroute.shp"
    #     routelinks_table = r"D:\TestLinearRef\riversroute_links.dbf"
    #
    #     dict_attr_field = {"id": "RID",
    #                        "length": "SHAPE@LENGTH",
    #                        }
    #     rivernet = tree.RiverNetwork.RiverNetwork(route_shapefile, routelinks_table, dict_attr_field)
    #     dict_attr_field = {"id": "OID",
    #                        "reach_id": "NewRID",
    #                        "dist": "MEAS",
    #                        "offset": "Distance"
    #                        }
    #     rivernet.add_points_collection(newtablepath, dict_attr_field)
    #
    #     lastpoint = None
    #     points_to_delete = []
    #     for reach in rivernet.browse_reaches():
    #         #print ("reach id:" + str(reach.id))
    #
    #         for point in reach.browse_points():
    #             #print ("point id:" + str(point.id))
    #             #print ("point distance:" + str(point.dist))
    #             #print ("point offset:" + str(point.offset))
    #             if lastpoint is not None and point.dist == lastpoint.dist and point.reach_id == lastpoint.reach_id:
    #                 print ("Duplicate point found!: " + str(point.id) + " and " + str(lastpoint.id))
    #                 if abs(point.offset) < abs(lastpoint.offset):
    #                     points_to_delete.append(lastpoint)
    #                 else:
    #                     points_to_delete.append(point)
    #
    #             lastpoint = point
    #     for point in points_to_delete:
    #         rivernet.delete_point(point)
    #
    #     dict_attr_field = {"id": ("ORIG_ID", "LONG"),
    #                        "reach_id": ("RID", "LONG"),
    #                        "dist": ("dist", "FLOAT"),
    #                        "offset": ("offset", "FLOAT"),
    #                        }
    #     rivernet.save_points(outputtable, dict_attr_field)
    #
    # finally:
    #     gc.CleanTempFiles()


    # Author: Mariana
    # Create near table to relate river routes and D8/D4 routes. When it is run once, it omits some links and other
    # in_features are linked to two different reaches from the near_feature layer. For fixing this issue, the tool has to
    # run twice (A to B and B to A). Then 2 clean-ups are required:
    # 1. Clean up of duplicate combinations
    # 2. Clean up wrong combination based on the number of intersections (points) between the two layers

    # Running Generate Near Table in both directions
    import arcpy
    # set workspace environment
    arcpy.env.workspace = r"D:\neartable"


# set required parameters for A-B
# in_features = r"D:\EtcheminFullSet\routesD8.shp\routes.shp"
# near_features = r"D:\EtcheminFullSet\routesD8.shp"
out_table = r"D:\neartable\routes_routes_D8.dbf"
#
# #create Near table
# arcpy.GenerateNearTable_analysis(in_features, near_features, out_table)

# set required parameters for B-A
in_features = r"D:\EtcheminFullSet\routesD8.shp\routes.shp"
near_features = r"D:\EtcheminFullSet\routesD8.shp"
out_table2 = r"D:\neartable\routesD8_routes.dbf"
# arcpy.GenerateNearTable_analysis(near_features, in_features, out_table2)

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
#arcpy.AddGeometryAttributes_management(intersectOut, "PART_COUNT")

# We joint out_table and out_table2 (they have the same fields where RID is the routeD8 ID and IN_FID is the route ID).
merge_out = r"D:\neartable\merge_out.dbf"
# arcpy.management.Merge([out_table, out_table2], merge_out)

# Clean-up 1: deleting duplicate rows from merge_out
# arcpy.DeleteIdentical_management(merge_out, ["IN_FID", "RID"])

# Clean-up 2: assign to each pair the correspondent value of intersection and dismiss the pair with the smallest count.
# Adding field COUNT to cleaned merge_out
#arcpy.management.AddField(merge_out, "COUNT", "LONG")
merge_out = r"D:\neartable\merge_out.dbf"
intersect = r"D:\neartable\intersect_table.dbf"
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

point_feature = r"D:\EtcheminFullSet\D8points_toproject.shp"
line_routes =  r"D:\TestLinearRef\routes_proj.shp"
out_table3 = r"D:\TestLinearRef\d8points_route_check3.dbf"
tol = "500 Meters"
props = "RID POINT meas"

arcpy.lr.LocateFeaturesAlongRoutes(point_feature, line_routes, "RouteID", tol, out_table3, props, "FIRST", "DISTANCE", "ZERO", "FIELDS", "M_DIRECTON")

# This is useful but not completely OK as the real process should be that if there are two combinations that have one
# element in common, the one with the lowest value should be eliminated. So, this process needs this adjustment


if __name__ == "__main__":
    # test comment
    # test 4
    messages = Messages()
    arcpy.env.overwriteOutput = True
    arcpy.env.scratchWorkspace = r"D:\TestLinearRef"

    # test_bed_assess()
    # test_1Dhydro()
    # test_treecreate()
    print (datetime.now())
    test_cursor()
    print (datetime.now())
