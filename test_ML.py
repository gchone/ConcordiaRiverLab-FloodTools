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
