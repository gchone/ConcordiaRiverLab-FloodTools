# coding: latin-1

# Fichier OurTreeSegment.py
# v0.0.2 - 24/10/2017

### Contenu ###
# classe OurTreeSegment : �tend la classe TreeSegment pour y ajouter la gestion des profils longitudinaux et
#   transversaux

### Historique des versions ###
# v0.0.1 - 18/09/2017 - Cr�ation - Gu�nol� Chon�
# v0.0.2 - 24/10/2017 - Description modifi�e - Gu�nol� Chon�


import TreeSegment
import ProfilePoint


class OurTreeSegment(TreeSegment.TreeSegment):

    def __init__(self, id):
        #   id : int - identifiant du segment
        TreeSegment.TreeSegment.__init__(self, id)
        # liste des points du profil longitudinal
        self.__ptsprofile = []

    def get_profile(self):
        return self.__ptsprofile

    def get_ptprofile(self, id):
        #   id : int - identifiant d'un point du profil longitudinal
        #   retour de la m�thode : ProfilePoint
        return self.__ptsprofile[id]

    def add_ptprofile(self, profilept):
        #   profilept : ProfilePoint - point du profil transversal � ajouter
        self.__ptsprofile.insert(0,profilept)

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


        newchild = OurTreeSegment(newid)
        childrenlist = []
        for child in self.get_childrens():
            childrenlist.append(child)
        for child in childrenlist:
            self.remove_child(child)
            newchild.add_child(child)
        self.add_child(newchild)
        self.add_child(segment)
        newchild.__ptsprofile = self.__ptsprofile[self.__ptsprofile.index(ptprofil)+1:]
        self.__ptsprofile = self.__ptsprofile[:self.__ptsprofile.index(ptprofil)+1]



    # def browsepts(self):
    #     if self.is_root():
    #         yield None, self.__ptsprofile[0]
    #     else:
    #         yield self.get_parent().__ptsprofile[-1], self.__ptsprofile[0]
    #     for i in range(1, len(self.__ptsprofile)):
    #         yield self.__ptsprofile[i - 1], self.__ptsprofile[i]
    #     for child in self.get_childrens():
    #         for ptprev, pt in child.browsepts():
    #             yield ptprev, pt


