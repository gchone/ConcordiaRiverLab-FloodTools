# -*- coding: utf-8 -*-

import tree.RiverNetwork
from BedAssessmentDirectLinearNet import *
from Simple1Dhydraulic import *
from datetime import datetime

class Messages():
    def addErrorMessage(self, text):
        print (text)

    def addWarningMessage(self, text):
        print (text)

    def addMessage(self, text):
        print(text)


def test_basic_network():

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
            point.z2 = point.z -100



def test_bed_assess():

    route = r"E:\InfoCrue\Refontebathy\SyntheticInputs\route.shp"
    routelinks = r"E:\InfoCrue\Refontebathy\SyntheticInputs\routelinks.dbf"


    points1 = r"E:\InfoCrue\Refontebathy\SyntheticInputs\memorytest\data13.dbf"
    #createtable = r"E:\InfoCrue\Refontebathy\SyntheticInputs\basicsolver_auto.dbf"
    createtable = r"E:\InfoCrue\Refontebathy\SyntheticInputs\memorytest\solverdata13.dbf"


    print ("start: "+str(datetime.now()))
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


    print ("loaded: "+str(datetime.now()))

    execute_BedAssessment(rivernet, "data", 0.03, 0.0001, messages)
    print("bed done: " + str(datetime.now()))

    #Enregistrement des données dans une nouvelle table
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

    print ("saved: "+str(datetime.now()))

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

    #Enregistrement des données dans une nouvelle table
    dict_attr_field = {"id": ("ORIG_ID", "LONG"),
                       "dist": ("MEAS", "FLOAT"),
                       "ws": ("ws", "FLOAT"),
                       }

    rivernet.save_points(createtable, dict_attr_field, "data")


if __name__ == "__main__":
    # test comment
    # test 3
    messages = Messages()
    arcpy.env.overwriteOutput = True

    #test_bed_assess()
    test_1Dhydro()