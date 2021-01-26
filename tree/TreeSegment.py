# -*- coding: utf-8 -*-



### Historique des versions ###
# v1.0 - Nov 2020 - Création - Guénolé Choné



class TreeSegment(object):

    ### Instance attributes ###
    # orientation: when using build_trees with a non-orientated network, flag for the orientation (True : good orientation)
    # length: total length of the reach



    def __init__(self, id):
        #   id : int - identifiant du segment
        self.__children = []
        self.id = id
        self.__parent = None

    def get_parent(self):
        #   retour de la méthode : TreeSegment - le segment parent (segment aval)
        return self.__parent


    def add_child(self, child):
        #   child : TreeSegment - segment à ajouter à la liste des segment amont
        self.__children.append(child)
        child.__parent = self


    def get_childrens(self):
        #   retour de la méthode : Liste de TreeSegment
        return self.__children


    def remove_child(self, child):
        self.__children.remove(child)
        child.__parent = None


    def is_root(self):
        # retour de la méthode : booléen
        return self.__parent == None


    def is_leaf(self):
        # retour de la méthode : booléen
        return len(self.get_childrens()) == 0


    def __str__(self):
        return self.__recursiveprint("")


    def __recursiveprint(self, prefix):
        string = prefix + str(self.id) + "\n"
        for child in self.get_childrens():
            string += child.__recursiveprint(prefix + "- ")
        return string



    # *** FONCTION A REMPLACER PAR DES GENERATORS ***
    # def get_profile(self):
    #     return self.__ptsprofile
    #
    #
    # def get_profile_uptodown(self):
    #     return list(reversed(self.__ptsprofile))




