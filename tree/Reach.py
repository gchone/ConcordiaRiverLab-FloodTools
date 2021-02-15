# -*- coding: utf-8 -*-



### Historique des versions ###
# v2.0 - Fev 2020 - Création - Guénolé Choné

from tree.NumpyArrayFedObject import *

class Reach(NumpyArrayFedObject):


    def __init__(self, rivernetwork, id):
        #   id : int - identifiant du segment
        self.id = id
        self.rivernetwork = rivernetwork

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





