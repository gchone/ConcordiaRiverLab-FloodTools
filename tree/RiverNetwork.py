# -*- coding: utf-8 -*-


### Historique des versions ###
# v2.0 - Fev 2020 - Création


from tree.Reach import *
from tree.DataPoint import *
import arcpy


class RiverNetwork(object):

    def __init__(self, reaches_shapefile, reaches_linktable, dict_attr_fields):

        self.__dict_attr_fields = dict_attr_fields
        self.__dict_points_collection = {}

        # on joint les deux tables


        # on initialise la matrice Numpy
        self.__numpyarray = arcpy.FeatureClassToNumPyArray(reaches_shapefile, [self.idfield, self.lenfield], null_value=-9999)

        # on ajoute un champ contenant une nouvelle instance de Reach


    def __get_downstream_reach(self, id):
        ### trouve et retourne le segment aval d'un segment dans la matrice Numpy  ###
        return None

    def __get_upstream_reaches(self, id):
        ### trouve et retourne la liste de segments amont d'un segment dans la matrice Numpy  ###
        return []

    def browse_reaches(self, orientation="DOWN_TO_UP", prioritize_points_collection = "MAIN", prioritize_points_attribute  = None, reverse = False):
        ### Générateur. Trouve et retourne la liste de segments dans la matrice Numpy  ###
        ### La matrice numpy est interrogée pour fournir les tronçons dans l'ordre souhaitée. Optionnellement, si
        ###     prioritize_points_attribute != None, l'ordre des tronçons retournés aux confluences est aussi déterminé.
        np_request_results = None # requete numpy
        for np_reachline in np_request_results:
            yield None # on retourne l'instance de Reach dans la matrice Numpy

    def __browse_points_in_reach(self, reachid, points_collection, orientation = "DOWN_TO_UP"):
        ### Générateur. Trouve et retourne la liste de points pour un segment dans la matrice Numpy  ###
        yield None

    def add_points_collection(self, points_shapefile, dict_attr_fields, points_collection_name="MAIN"):
        # Ajout d'une nouvelle collection de points
        self.__dict_points_collection[points_collection_name] = self.Points_collection(points_shapefile, dict_attr_fields)

    def get_points_collections_names(self):
        # encapsultion du dictionnaire __dict_attr_fields
        return self.__dict_attr_fields.keys()

    def get_points_collection(self, name="MAIN"):
        # encapsultion du dictionnaire __dict_attr_fields
        return self.__dict_attr_fields[name]

    def save_points(self, target_shapefile, dict_attr_fields, points_collection_name="MAIN"):
        ### sauvegarde les points dans un nouveau shapefile
        return

class Points_collection(object):

    def __init__(self, points_shapefile, dict_attr_fields):
        ### on initialise la matrice Numpy, avec un champ supplémentaire contenant une nouvelle instance de DataPoint ###
        ### self.__numpyarray =
        self.__dict_attr_fields = dict_attr_fields
