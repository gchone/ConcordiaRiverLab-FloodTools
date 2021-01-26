# coding: latin-1



### Historique des versions ###
# v1.0 - Nov 2020 - Création - Guénolé Choné



class LinearTreeSegment(object):

    ### Instance attributes ###
    # orientation: when using build_trees with a non-orientated network, flag for the orientation (True : good orientation)
    # length: total length of the reach



    def __init__(self, id):
        #   id : int - identifiant du segment
        self.__children = []
        self.id = id
        self.__parent = None
        self.__ptsprofile = []

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


    def get_profile(self):
        return self.__ptsprofile


    def get_ptprofile_pos(self, cs):
        #   retour de la méthode : position du ProfilePoint
        return self.__ptsprofile.index(cs)


    def get_ptprofile_bypos(self, pos):
        #   pos : int - identifiant d'un point du profil longitudinal
        #   retour de la méthode : ProfilePoint
        return self.__ptsprofile[pos]


    def get_profile_uptodown(self):
        return list(reversed(self.__ptsprofile))


    def delete_ptprofile(self, pt):
        self.__ptsprofile.remove(pt)


    def add_ptprofile(self, profilept):
        #   profilept : ProfilePoint - point du profil transversal à ajouter
        self.__ptsprofile.insert(0, profilept)


    def fork(self, segment, newid, ptprofil):
        # the current segment become the downstream (parent) one
        # the added segment is a child
        # a new child segment is created

        # newparent = OurTreeSegment(newid)
        # if not self.is_root():
        #     self.get_parent().add_child(newparent)
        #     self.get_parent().remove_child(self)
        # newparent.add_child(self)
        # newparent.add_child(segment)
        # newparent.__ptsprofile = self.__ptsprofile[:self.__ptsprofile.index(ptprofil)+1]
        # self.__ptsprofile = self.__ptsprofile[self.__ptsprofile.index(ptprofil)+1:]


        newchild = LinearTreeSegment(newid)
        childrenlist = []
        for child in self.get_childrens():
            childrenlist.append(child)
        for child in childrenlist:
            self.remove_child(child)
            newchild.add_child(child)
        self.add_child(newchild)
        self.add_child(segment)
        newchild.__ptsprofile = self.__ptsprofile[self.__ptsprofile.index(ptprofil) + 1:]
        self.__ptsprofile = self.__ptsprofile[:self.__ptsprofile.index(ptprofil) + 1]

