# -*- coding: utf-8 -*-
import copy

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
        self.dict_points_collection = {}

        # on initialise les matrices Numpy
        # matrice de base
        tempnumpyarray = arcpy.da.FeatureClassToNumPyArray(reaches_shapefile, list(dict_attr_fields.values()), null_value=-9999)
        newdtype = []
        for name, dtype in tempnumpyarray.dtype.fields.items():
            newdtype.append((name, dtype[0]))
        newdtype.append(('object', 'O'))
        self._numpyarray = np.empty(tempnumpyarray.shape[0], newdtype)
        for field in self._dict_attr_fields.values():
            self._numpyarray[field] = tempnumpyarray[field]
        del tempnumpyarray

        # matrice des liaisons amont-aval
        self._numpyarraylinks = arcpy.da.TableToNumPyArray(reaches_linktable, [self.reaches_linkfielddown, self.reaches_linkfieldup])

        # In order to populate the object in the array, we need to iterate with a SearchCursor so we can retrieve the Shape object, which could be needed
        reachescursor = arcpy.da.SearchCursor(reaches_shapefile, [self._dict_attr_fields['id'], "SHAPE@"])
        for reach in reachescursor:
            self._numpyarray['object'][reach[0]] = Reach(self, reach[1], self._numpyarray[self._numpyarray[self._dict_attr_fields['id']] == reach[0]][0])

        # Tried different things to add a field with the objects to the _numpyarray but did not succeed:
        #self._numpyarray = rfn.merge_arrays([self._numpyarray, object_column], flatten=True)
        #rfn.append_fields(self._numpyarray, 'object', list)

    def get_downstream_ends(self):
        # Générateur. Retourne la liste des tronçons extrémités aval
        # Ce sont ceux qui ne sont pas présents dans "UpstreamRID" de _numpyarraylinks
        for id in np.setdiff1d(self._numpyarray[self._dict_attr_fields['id']], self._numpyarraylinks[self.reaches_linkfieldup]):
            yield self._numpyarray[self._numpyarray[self._dict_attr_fields['id']] == id]['object'][0]

    def get_upstream_ends(self):
        # Générateur. Retourne la liste des tronçons extrémités amont
        # Ce sont ceux qui ne sont pas présents dans "DownsstreamRID" de _numpyarraylinks
        for id in np.setdiff1d(self._numpyarray[self._dict_attr_fields['id']], self._numpyarraylinks[self.reaches_linkfielddown]):
            yield self._numpyarray[self._numpyarray[self._dict_attr_fields['id']] == id]['object'][0]

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
        self.dict_points_collection[points_collection_name] = Points_collection(points_collection_name, self, points_table, dict_attr_fields)



    def get_points_collections_names(self):
        # encapsultion du dictionnaire _dict_points_collection
        return self.dict_points_collection.keys()

    def _get_points_collection(self, name="MAIN"):
        # encapsultion du dictionnaire _dict_points_collection
        return self.dict_points_collection[name]

    def save_points(self, target_table, dict_attr_fields, points_collection_name="MAIN"):
        # sauvegarde les points dans une nouvelle table
        if arcpy.Exists(target_table) and arcpy.env.overwriteOutput == True:
            arcpy.Delete_management(target_table)

        # Below solution works, but too slow
        # Cursors can't be used. Solution could be to create and populate a numpy array

        # arcpy.CreateTable_management(os.path.dirname(target_table), os.path.basename(target_table))
        #
        # listfields = []
        # for attribute, addfield_params in dict_attr_fields.items():
        #     listfields.append(addfield_params[0])
        #     if addfield_params[1] == "TEXT":
        #         arcpy.AddField_management(target_table, addfield_params[0], addfield_params[1],
        #                                   field_length=addfield_params[2])
        #     else:
        #         arcpy.AddField_management(target_table, addfield_params[0], addfield_params[1])
        # pointcursor = arcpy.da.InsertCursor(target_table, listfields)
        #
        # for point in self._dict_points_collection[points_collection_name]._points['object']:
        #     datalist = []
        #     for attribute, addfield_params in dict_attr_fields.items():
        #         datalist.append(getattr(point, attribute))
        #     pointcursor.insertRow(datalist)

        # Gather metadata for the new array
        collection = self.dict_points_collection[points_collection_name]
        originalarray = collection._numpyarray
        newdtype = []
        idfield = None
        for field, value in dict_attr_fields.items():
            if value[1] == "FLOAT":
                newdtype.append((value[0], 'f8'))
            if value[1] == "LONG":
                newdtype.append((value[0], 'i4'))
            if value[1] == "TEXT":
                newdtype.append((value[0], 'U'+str(value[2])))
            if field == "id":
                idfield = value[0]
        if idfield is None:
            raise RuntimeError("'id' field is required")
        # Create a new array
        newarray = np.empty(originalarray.shape[0], dtype=newdtype)
        # Populate the array
        required_attr = []
        for field, value in dict_attr_fields.items():
            if field in collection._dict_attr_fields.keys():
                # if the data is in the _numpyarray, than we just need to copy it
                newarray[value[0]] = originalarray[collection._dict_attr_fields[field]]
            else:
                required_attr.append((field, value[0]))
        # we need to browse the data point object for accessing the remaining data
        for row in originalarray:
            for attribute in required_attr:
                newarray[attribute[1]][newarray[idfield] == id] = getattr(row["object"], attribute[0])
        # saving
        arcpy.da.NumPyArrayToTable(newarray, target_table)


    def __str__(self):
        for downstream_end in self.get_downstream_ends():
            return downstream_end._recursiveprint("")


    def delete_point(self, datapoint):
        collection = datapoint._pointscollection
        collection._numpyarray = collection._numpyarray[collection._numpyarray[collection._dict_attr_fields['id']]!=datapoint.id]




class _NumpyArrayFedObject(object):


    def __init__(self, numpyarray_holder, data):
        # The object can be fed by an id, or by it's all row from the numpyarray
        # Note: __dict__ is called to prevent infinite recursion linked with __getattr__/__setattr__
        self.__dict__["_numpyarray_holder"] = numpyarray_holder

        for attr, field in self._numpyarray_holder._dict_attr_fields.items():
            self.__dict__[attr] = data[field]


    def __setattr__(self, name, value):
        if name != "id" and name in self._numpyarray_holder._dict_attr_fields.keys():
            # change la valeur dans la matrice Numpy pour
            array = self._numpyarray_holder._numpyarray
            # champ pour l'id:
            idfield = self._numpyarray_holder._dict_attr_fields['id']
            # champ pour la valeur:
            valuefield = self._numpyarray_holder._dict_attr_fields[name]
            array[valuefield][array[idfield] == self.id] = value

        super(_NumpyArrayFedObject, self).__setattr__(name, value)

    # As the object is within a numpy array, np.sort tries to compare objects.
    # This method overloads the '<' operator
    def __lt__(self, other):
        return True


class Reach(_NumpyArrayFedObject):

    def __init__(self, rivernetwork, shape, data):
        _NumpyArrayFedObject.__init__(self, rivernetwork, data)
        self.rivernetwork = rivernetwork
        self.shape = shape

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
            return self.rivernetwork._numpyarray[self.rivernetwork._numpyarray[self.rivernetwork._dict_attr_fields['id']] == list_iddown[0]]['object'][0]
        else:
            return None

    def get_uptream_reaches(self):
        #   Générateur de Reach
        list_idup = self.rivernetwork._numpyarraylinks[self.rivernetwork._numpyarraylinks[self.rivernetwork.reaches_linkfielddown] == self.id][
            self.rivernetwork.reaches_linkfieldup]
        for id in list_idup:
            yield self.rivernetwork._numpyarray[self.rivernetwork._numpyarray[self.rivernetwork._dict_attr_fields['id']] == id]['object'][0]


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
        collection = self.rivernetwork.dict_points_collection[points_collection]
        if orientation == "DOWN_TO_UP":
            sortedlist = np.sort(collection._numpyarray[collection._numpyarray[collection._dict_attr_fields['reach_id']] == self.id], order=collection._dict_attr_fields['dist'])
        else:
            sortedlist = np.sort(
                collection._numpyarray[collection._numpyarray[collection._dict_attr_fields['reach_id']] == self.id], order=collection._dict_attr_fields['dist'])
            sortedlist=np.flipud(sortedlist)
        for row in sortedlist:
           yield row['object']

    def get_last_point(self, points_collection="MAIN"):
        collection = self.rivernetwork.dict_points_collection[points_collection]
        sortedlist = np.sort(
            collection._numpyarray[collection._numpyarray[collection._dict_attr_fields['reach_id']] == self.id], order=collection._dict_attr_fields['dist'])
        if len(sortedlist) > 0:
            return sortedlist['object'][-1]
        else:
            return None

    def add_point(self, distance, offset, points_collection):

        collection = self.rivernetwork._get_points_collection(points_collection)
        #Find the max currently used id in the collection, and add 1
        newid = numpy.max(collection._numpyarray[collection._dict_attr_fields['id']]) + 1
        #Add a row in the two numpy arrays
        to_add = numpy.empty(1, dtype=collection._numpyarray.dtype)
        to_add[collection._dict_attr_fields['id']] = newid
        to_add[collection._dict_attr_fields['dist']] = distance
        to_add[collection._dict_attr_fields['offset']] = offset
        to_add[collection._dict_attr_fields['reach_id']] = self.id
        datapoint = DataPoint(collection, self, to_add)
        to_add['object'] = datapoint
        collection._numpyarray = numpy.append(collection._numpyarray, to_add)

        return datapoint




class Points_collection(object):

    def __init__(self, name, rivernetwork, points_table=None, dict_attr_fields=None):
        self.name = name
        self.rivernetwork = rivernetwork
        if points_table is not None and dict_attr_fields is not None:
            self._dict_attr_fields = dict_attr_fields
            # matrice de base
            tempnumpyarray =  arcpy.da.TableToNumPyArray(points_table, list(dict_attr_fields.values()), null_value=-9999)
            newdtype = []
            for name, dtype in tempnumpyarray.dtype.fields.items():
                newdtype.append((name, dtype[0]))
            newdtype.append(('object', 'O'))
            self._numpyarray = np.empty(tempnumpyarray.shape[0], newdtype)
            for field in self._dict_attr_fields.values():
                self._numpyarray[field] = tempnumpyarray[field]
            del tempnumpyarray

            for row in self._numpyarray:
                reachid = row[self._dict_attr_fields['reach_id']]
                reach = self.rivernetwork._numpyarray[self.rivernetwork._numpyarray[self.rivernetwork._dict_attr_fields['id']] == reachid]['object'][0]
                row['object'] = DataPoint(self, reach, row)
        else:
            self._dict_attr_fields = {"id": "id",
                                      "reach_id": "RID",
                                      "dist": "dist",
                                      "offset": "offset"}
            self._numpyarray = np.empty(0, dtype=[('id', 'i4'), ('RID', 'i4'), ('dist', 'f8'), ('offset', 'f8'), ('object', 'O')])

class DataPoint(_NumpyArrayFedObject):
    def __init__(self, pointscollection, reach, data):
        _NumpyArrayFedObject.__init__(self, pointscollection, data)
        self.collectionname = pointscollection.name
        self._pointscollection = pointscollection
        self.reach = reach
