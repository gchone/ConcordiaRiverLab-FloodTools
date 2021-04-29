# -*- coding: utf-8 -*-


### Historique des versions ###
# v2.0 - Fev 2020 - Création


import arcpy
import numpy
import numpy as np
import os
import numpy.lib.recfunctions as rfn

class RiverNetwork(object):

    reaches_linkfieldup = "UpID"
    reaches_linkfielddown = "DownID"

    def __init__(self, reaches_shapefile, reaches_linktable, dict_attr_fields):

        self._dict_attr_fields = dict_attr_fields
        self._dict_points_collection = {}

        # on initialise les matrices Numpy
        # matrice de base
        self._numpyarray = arcpy.da.FeatureClassToNumPyArray(reaches_shapefile, dict_attr_fields.values(), null_value=-9999)
        # matrice des liaisons amont-aval
        self._numpyarraylinks = arcpy.da.TableToNumPyArray(reaches_linktable, [self.reaches_linkfielddown, self.reaches_linkfieldup])
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
        for id in np.setdiff1d(self._reaches['id'], self._numpyarraylinks[self.reaches_linkfieldup]):
            yield self._reaches[self._reaches['id'] == id]['object'][0]

    def get_upstream_ends(self):
        # Générateur. Retourne la liste des tronçons extrémités amont
        # Ce sont ceux qui ne sont pas présents dans "DownsstreamRID" de _numpyarraylinks
        for id in np.setdiff1d(self._reaches['id'], self._numpyarraylinks[self.reaches_linkfielddown]):
            yield self._reaches[self._reaches['id'] == id]['object'][0]

    def browse_reaches(self, orientation="DOWN_TO_UP", prioritize_points_collection = "MAIN", prioritize_points_attribute  = None, reverse = False):
        # Générateur. Trouve et retourne la liste de segments dans la matrice Numpy
        # La matrice numpy est interrogée pour fournir les tronçons dans l'ordre souhaitée. Optionnellement, si
        #     prioritize_points_attribute != None, l'ordre des tronçons retournés aux confluences est aussi déterminé.
        if orientation=="DOWN_TO_UP":
            for downstream_end in self.get_downstream_ends():
                for item in downstream_end._recursive_browse_reaches(orientation, prioritize_points_collection, prioritize_points_attribute, reverse):
                    yield item
        else:
            for upstream_end in self.get_upstream_ends():
                for item in upstream_end._recursive_browse_reaches(orientation, prioritize_points_collection, prioritize_points_attribute, reverse):
                    yield item

    def add_points_collection(self, points_table=None, dict_attr_fields=None, points_collection_name="MAIN"):
        # Ajout d'une nouvelle collection de points
        self._dict_points_collection[points_collection_name] = _Points_collection(points_collection_name, points_table, dict_attr_fields)



    def get_points_collections_names(self):
        # encapsultion du dictionnaire _dict_points_collection
        return self._dict_points_collection.keys()

    def get_points_collection(self, name="MAIN"):
        # encapsultion du dictionnaire _dict_points_collection
        return self._dict_points_collection[name]

    def save_points(self, target_table, dict_attr_fields, points_collection_name="MAIN"):
        # sauvegarde les points dans une nouvelle table
        if arcpy.Exists(target_table) and arcpy.env.overwriteOutput == True:
            arcpy.Delete_management(target_table)
        arcpy.CreateTable_management(os.path.dirname(target_table), os.path.basename(target_table))

        listfields = []
        for attribute, addfield_params in dict_attr_fields.items():
            listfields.append(addfield_params[0])
            if addfield_params[1] == "TEXT":
                arcpy.AddField_management(target_table, addfield_params[0], addfield_params[1],
                                          field_length=addfield_params[2])
            else:
                arcpy.AddField_management(target_table, addfield_params[0], addfield_params[1])
        pointcursor = arcpy.da.InsertCursor(target_table, listfields)

        for point in self._dict_points_collection[points_collection_name]._points['object']:
            datalist = []
            for attribute, addfield_params in dict_attr_fields.items():
                datalist.append(getattr(point, attribute))
            pointcursor.insertRow(datalist)


    def __str__(self):
        for downstream_end in self.get_downstream_ends():
            return downstream_end._recursiveprint("")


class _NumpyArrayFedObject(object):


    def __init__(self, numpyarray_holder, id):
        # Appel à __dict__ fait pour éviter la récursion infinie liée à __getattr__/__setattr__
        self.__dict__["_numpyarray_holder"] = numpyarray_holder
        self.__dict__["id"]  = id


    def __getattr__(self, name):
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
        if orientation == "DOWN_TO_UP":
            for reach in self.get_uptream_reaches():
                for item in reach._recursive_browse_reaches(orientation, prioritize_points_collection,
                                       prioritize_points_attribute, reverse):
                    yield item
        else:
            downstreamreach = self.get_downstream_reach()
            if downstreamreach is not None:
                for item in downstreamreach._recursive_browse_reaches(orientation, prioritize_points_collection,
                                           prioritize_points_attribute, reverse):
                    yield item

    def get_downstream_reach(self):
        # doit trouver le parent dans rivernetwork
        list_iddown = self.rivernetwork._numpyarraylinks[self.rivernetwork._numpyarraylinks[self.rivernetwork.reaches_linkfieldup] == self.id][
            self.rivernetwork.reaches_linkfielddown]
        if len(list_iddown)>0:
            return self.rivernetwork._reaches[self.rivernetwork._reaches['id'] == list_iddown[0]]['object'][0]
        else:
            return None

    def get_uptream_reaches(self):
        #   Générateur de Reach
        list_idup = self.rivernetwork._numpyarraylinks[self.rivernetwork._numpyarraylinks[self.rivernetwork.reaches_linkfielddown] == self.id][
            self.rivernetwork.reaches_linkfieldup]
        for id in list_idup:
            yield self.rivernetwork._reaches[self.rivernetwork._reaches['id'] == id]['object'][0]


    def is_downstream_end(self):
        # retour de la méthode : booléen
        return self.get_downstream_reach() == None

    def is_upstream_end(self):
        # retour de la méthode : booléen
        return len(list(self.get_uptream_reaches())) == 0

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
        if orientation == "DOWN_TO_UP":
            sortedlist = np.sort(collection._numpyarray[collection._numpyarray[collection._dict_attr_fields['reach_id']] == self.id], order=collection._dict_attr_fields['dist'])
        else:
            sortedlist = np.sort(
                collection._numpyarray[collection._numpyarray[collection._dict_attr_fields['reach_id']] == self.id],
                order=collection._dict_attr_fields['dist'])
            sortedlist=np.flipud(sortedlist)
        for id in sortedlist[collection._dict_attr_fields['id']]:
           yield collection._points[collection._points['id'] == id]['object'][0]

    def get_last_point(self, points_collection="MAIN"):
        collection = self.rivernetwork._dict_points_collection[points_collection]
        sortedlist = np.sort(
            collection._numpyarray[collection._numpyarray[collection._dict_attr_fields['reach_id']] == self.id],
            order=collection._dict_attr_fields['dist'])
        if len(sortedlist) > 0:
            lastid = sortedlist[collection._dict_attr_fields['id']][-1]
            return collection._points[collection._points['id'] == lastid]['object'][0]
        else:
            return None

    def add_point(self, datapoint, points_collection="MAIN"):
        collection = self.rivernetwork._dict_points_collection[points_collection]

        #to_add = np.array([(2, Points_collection("ff"))], dtype=a.dtype)


class _Points_collection(object):

    def __init__(self, name, points_table=None, dict_attr_fields=None):
        self.name = name
        if points_table is not None and dict_attr_fields is not None:
            self._dict_attr_fields = dict_attr_fields
            # matrice de base
            self._numpyarray = arcpy.da.TableToNumPyArray(points_table, dict_attr_fields.values(), null_value=-9999)
            print self._numpyarray
            print self._numpyarray.dtype
            print self._numpyarray.shape
            # matrice contenant les instances de DataPoint
            self._points = np.empty(self._numpyarray.shape[0], dtype=[('id', 'i4'), ('object', 'O')])
            for i in range(self._numpyarray.shape[0]):
                self._points[i]['id'] = self._numpyarray[i][self._dict_attr_fields['id']]
                self._points[i]['object'] = DataPoint(self, self._numpyarray[i][self._dict_attr_fields['id']])
        else:
            self._dict_attr_fields = {"id": "id",
                                      "reach_id": "RID",
                                      "dist": "dist",
                                      "offset": "offset",}
            self._numpyarray = np.empty(0, dtype=[('id', 'i4'), ('RID', 'i4'), ('dist', 'f4'), ('offset', 'f4')])
            self._points = np.empty(0, dtype=[('id', 'i4'), ('object', 'O')])

class DataPoint(_NumpyArrayFedObject):
    def __init__(self, pointscollection, id):
        _NumpyArrayFedObject.__init__(self, pointscollection, id)
        self.pointscollection = pointscollection
