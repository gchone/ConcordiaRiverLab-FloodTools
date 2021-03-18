# -*- coding: utf-8 -*-


### Historique des versions ###
# v2.0 - Fev 2020 - Création


from tree.Reach import *
from tree.DataPoint import *
import arcpy
import numpy as np
import numpy.lib.recfunctions as rfn

class RiverNetwork(object):

    reaches_linkfieldup = "UpstreamRID"
    reaches_linkfielddown = "DownstreamRID"

    def __init__(self, reaches_shapefile, reaches_linktable, dict_attr_fields):

        self.__dict_attr_fields = dict_attr_fields
        self.__dict_points_collection = {}

        # on initialise les matrices Numpy
        self.__numpyarray = arcpy.FeatureClassToNumPyArray(reaches_shapefile, dict_attr_fields.values(), null_value=-9999)
        self.__numpyarraylinks = arcpy.da.TableToNumPyArray(reaches_linktable, [self.reaches_linkfielddown, self.reaches_linkfieldup])


        # on ajoute un champ contenant une nouvelle instance de Reach
        object_column = np.empty(self.__numpyarray.shape[0], 'object', dtype=object)
        self.__numpyarray = rfn.merge_arrays((self.__numpyarray, object_column), flatten=True)
        for row in self.__numpyarray:
            row['object'] = Reach(self, row[self.__dict_attr_fields[self.idkey]])


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


class NumpyArrayFedObject(object):

    idkey = "id"

    def __init__(self, numpyarray_holder):
        self.__numpyarray_holder = numpyarray_holder

    def __getattribute__(self, name):
        try:
            # retourne la valeur lue dans la matrice Numpy
            array = self.numpyarray_holder.__numpyarray
            # champ pour l'id:
            idfield = self.numpyarray_holder.__dict_attr_fields[self.idkey]
            # champ pour la valeur:
            valuefield = self.numpyarray_holder.__dict_attr_fields[name]

            return array[array[idfield] == self.id][valuefield][0]
        except KeyError:
            # si ce n'est pas dans la matrice numpy, on regarde dans les attributs normaux
            return super(NumpyArrayFedObject, self).__getattribute__(name)

    def __setattr__(self, name, value):
        try:
            # change la valeur dans la matrice Numpy pour
            array = self.numpyarray_holder.__numpyarray
            # champ pour l'id:
            idfield = self.numpyarray_holder.__dict_attr_fields[self.idkey]
            # champ pour la valeur:
            valuefield = self.numpyarray_holder.__dict_attr_fields[name]
            array[array[idfield] == self.id][valuefield] = value
        except KeyError:
            # si ce n'est pas dans la matrice numpy, on modifie les attributs normaux
            super(NumpyArrayFedObject, self).__setattr__(name, value)


class Reach(NumpyArrayFedObject):

    def __init__(self, rivernetwork, id):
        #   id : int - identifiant du segment
        self.id = id
        self.rivernetwork = rivernetwork
        NumpyArrayFedObject.__init__(self, rivernetwork)

    def get_downstream_reach(self):
        # doit trouver le parent dans rivernetwork
        return self.rivernetwork._get_downstream_reach(self.id)

    def get_uptream_reaches(self):
        #   retour de la méthode : Liste de Reach
        return self.rivernetwork._get_upstream_reaches(self.id)

    def is_downstream_end(self):
        # retour de la méthode : booléen
        return self.get_downstream_reach() == None

    def is_upstream_end(self):
        # retour de la méthode : booléen
        return len(self.get_uptream_reaches()) == 0

    def __str__(self):
        return self.__recursiveprint("")

    def __recursiveprint(self, prefix):
        string = prefix + str(self.id) + "\n"
        for child in self.get_uptream_reaches():
            string += child.__recursiveprint(prefix + "- ")
        return string

    def browse_points(self, points_collection="MAIN", orientation="DOWN_TO_UP"):
        for point in self.rivernetwork.__browse_points_in_reach(self.id, points_collection, orientation="DOWN_TO_UP"):
            yield point


class Points_collection(object):
    def __init__(self, points_shapefile, dict_attr_fields):
        ### on initialise la matrice Numpy, avec un champ supplémentaire contenant une nouvelle instance de DataPoint ###
        ### self.__numpyarray =
        self.__dict_attr_fields = dict_attr_fields


class DataPoint(NumpyArrayFedObject):
    def __init__(self, id, downstream_point, reach, pointscollection):
        self.downstream_point = downstream_point
        self.id = id
        self.reach = reach
        self.pointscollection = pointscollection
        NumpyArrayFedObject.__init__(self, pointscollection)