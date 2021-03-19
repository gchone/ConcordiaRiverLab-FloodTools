# -*- coding: utf-8 -*-


### Historique des versions ###
# v2.0 - Fev 2020 - Création


import arcpy
import numpy as np
import numpy.lib.recfunctions as rfn

class RiverNetwork(object):

    _reaches_linkfieldup = "UpstreamRID"
    _reaches_linkfielddown = "DownstreamRID"

    def __init__(self, reaches_shapefile, reaches_linktable, dict_attr_fields):

        self._dict_attr_fields = dict_attr_fields
        self._dict_points_collection = {}

        # on initialise les matrices Numpy
        # matrice de base
        self._numpyarray = arcpy.da.FeatureClassToNumPyArray(reaches_shapefile, dict_attr_fields.values(), null_value=-9999)
        # matrice des liaisons amont-aval
        self._numpyarraylinks = arcpy.da.TableToNumPyArray(reaches_linktable, [self._reaches_linkfielddown, self._reaches_linkfieldup])
        # matrice contenant les instances de Reach
        self._reaches = np.empty(self._numpyarray.shape[0], dtype=[('id', 'i4'),('object', 'O')])
        for i in range(self._numpyarray.shape[0]):
            self._reaches[i]['id'] = self._numpyarray[i][self._dict_attr_fields['id']]
            self._reaches[i]['object'] = Reach(self, self._numpyarray[i][self._dict_attr_fields['id']])
        # Tried different things to add a field with the objects to the _numpyarray but did not succeed
        #self._numpyarray = rfn.merge_arrays([self._numpyarray, object_column], flatten=True)
        #rfn.append_fields(self._numpyarray, 'object', list)

    def get_downstream_ends(self):
        # Générateur. Retourne la liste des tronçons extrémités aval
        # Ce sont ceux qui ne sont pas présents dans "UpstreamRID" de _numpyarraylinks
        for id in np.setdiff1d(self._reaches['id'], self._numpyarraylinks[self._reaches_linkfieldup]):
            yield self._reaches[self._reaches['id'] == id]['object'][0]

    def browse_reaches(self, orientation="DOWN_TO_UP", prioritize_points_collection = "MAIN", prioritize_points_attribute  = None, reverse = False):
        # Générateur. Trouve et retourne la liste de segments dans la matrice Numpy
        # La matrice numpy est interrogée pour fournir les tronçons dans l'ordre souhaitée. Optionnellement, si
        #     prioritize_points_attribute != None, l'ordre des tronçons retournés aux confluences est aussi déterminé.
        for downstream_end in self.get_downstream_ends():
            for item in downstream_end._recursive_browse_reaches(orientation, prioritize_points_collection, prioritize_points_attribute, reverse):
                yield item

    def add_points_collection(self, points_shapefile, dict_attr_fields, points_collection_name="MAIN"):
        # Ajout d'une nouvelle collection de points
        self._dict_points_collection[points_collection_name] = Points_collection(points_shapefile, dict_attr_fields)

    def get_points_collections_names(self):
        # encapsultion du dictionnaire _dict_points_collection
        return self._dict_points_collection.keys()

    def get_points_collection(self, name="MAIN"):
        # encapsultion du dictionnaire _dict_points_collection
        return self._dict_points_collection[name]

    def save_points(self, target_shapefile, dict_attr_fields, points_collection_name="MAIN"):
        ### sauvegarde les points dans un nouveau shapefile
        return

    def __str__(self):
        for downstream_end in self.get_downstream_ends():
            return downstream_end._recursiveprint("")


class _NumpyArrayFedObject(object):


    def __init__(self, numpyarray_holder, id):
        # Appel à __dict__ fait pour éviter la récursion infinie liée à __getattr__/__setattr__
        self.__dict__["_numpyarray_holder"] = numpyarray_holder
        self.__dict__["id"]  = id


    def __getattr__(self, name):
        # if name == "id" or name == "__numpyarray_holder" or name not in self.__numpyarray_holder.keys():
        #     return super(NumpyArrayFedObject, self).__getattribute__(name)
        # else:
        # retourne la valeur lue dans la matrice Numpy
        array = self._numpyarray_holder._numpyarray
        # champ pour l'id:
        idfield = self._numpyarray_holder._dict_attr_fields['id']
        # champ pour la valeur:
        valuefield = self._numpyarray_holder._dict_attr_fields[name]

        return array[array[idfield] == self.id][valuefield][0]


    def __setattr__(self, name, value):
        if name != "id" and name in self._numpyarray_holder._dict_attr_fields.keys():
            # change la valeur dans la matrice Numpy pour
            array = self._numpyarray_holder._numpyarray
            # champ pour l'id:
            idfield = self._numpyarray_holder._dict_attr_fields['id']
            # champ pour la valeur:
            valuefield = self._numpyarray_holder._dict_attr_fields[name]
            array[array[idfield] == self.id][valuefield] = value
        else:
            super(_NumpyArrayFedObject, self).__setattr__(name, value)



class Reach(_NumpyArrayFedObject):

    def __init__(self, rivernetwork, id):
        #   id : int - identifiant du segment
        _NumpyArrayFedObject.__init__(self, rivernetwork, id)
        self.rivernetwork = rivernetwork

    def _recursive_browse_reaches(self, orientation, prioritize_points_collection,
                                   prioritize_points_attribute, reverse):
        yield self
        for reach in self.get_uptream_reaches():
            for item in reach._recursive_browse_reaches(orientation, prioritize_points_collection,
                                   prioritize_points_attribute, reverse):
                yield item

    def get_downstream_reach(self):
        # doit trouver le parent dans rivernetwork
        return self.rivernetwork._get_downstream_reach(self.id)

    def get_uptream_reaches(self):
        #   Générateur de Reach
        list_idup = self.rivernetwork._numpyarraylinks[self.rivernetwork._numpyarraylinks[self.rivernetwork._reaches_linkfielddown] == self.id][
            self.rivernetwork._reaches_linkfieldup]
        for id in list_idup:
            yield self.rivernetwork._reaches[self.rivernetwork._reaches['id'] == id]['object'][0]


    def is_downstream_end(self):
        # retour de la méthode : booléen
        return self.get_downstream_reach() == None

    def is_upstream_end(self):
        # retour de la méthode : booléen
        return len(self.get_uptream_reaches()) == 0

    def __str__(self):
        return str(self.id)

    def _recursiveprint(self, prefix):
        string = prefix + str(self) + "\n"
        for child in self.get_uptream_reaches():
            string += child.__recursiveprint(prefix + "- ")
        return string

    def browse_points(self, points_collection="MAIN", orientation="DOWN_TO_UP"):
        #   Générateur de DataPoint
        collection = self.rivernetwork._dict_points_collection[points_collection]
        sortedlist = np.sort(collection._numpyarray[collection._numpyarray[collection._dict_attr_fields['reach_id']] == self.id], order=collection._dict_attr_fields['dist'])
        for id in sortedlist[collection._dict_attr_fields['id']]:
           yield collection._points[collection._points['id'] == id]['object'][0]



class Points_collection(object):

    def __init__(self, points_shapefile, dict_attr_fields):
        self._dict_attr_fields = dict_attr_fields
        # matrice de base
        self._numpyarray = arcpy.da.TableToNumPyArray(points_shapefile, dict_attr_fields.values(), null_value=-9999)
        # matrice contenant les instances de DataPoint
        self._points = np.empty(self._numpyarray.shape[0], dtype=[('id', 'i4'), ('object', 'O')])
        for i in range(self._numpyarray.shape[0]):
            self._points[i]['id'] = self._numpyarray[i][self._dict_attr_fields['id']]
            self._points[i]['object'] = DataPoint(self, self._numpyarray[i][self._dict_attr_fields['id']])

class DataPoint(_NumpyArrayFedObject):
    def __init__(self, pointscollection, id):
        _NumpyArrayFedObject.__init__(self, pointscollection, id)
        self.pointscollection = pointscollection
