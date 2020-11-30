# coding: latin-1

# Fichier TreeManager.py
# v0.0.2 - 24/10/2017

### Contenu ###
# classe TreeManager : Classe abstraite de gestion g�n�rique d'un arbre (m�thodes d'int�rogation sur l'ensemble de
#   l'arbre)

### Historique des versions ###
# v0.0.1 - 03/10/2017 - Cr�ation
# v0.0.2 - 24/10/2017 - Description modifi�e - Gu�nol� Chon�
# v0.1 - Nov 2020 - Ajout du parcours des segments d'amont vers l'aval


class TreeManager(object):

    def __init__(self):
        self.treeroot = None

    def treesegments(self):
        #   retour de la m�thode : G�n�rateur de TreeSegment
        for n in self.__recursivetreesegments(self.treeroot):
            yield n

    def treesegments_uptodown(self):
        #   retour de la m�thode : G�n�rateur de TreeSegment
        for leaf in self.leaves():
            for n in self.__recursivetreesegments_uptodown(leaf):
                yield n

    def __recursivetreesegments(self, treesegment):
        #   treesegment : TreeSegment - Segment � retourner, ainsi que ces enfants (segments amont)
        #   retour de la m�thode : G�n�rateur de TreeSegment
        yield treesegment
        for child in treesegment.get_childrens():
            for n in self.__recursivetreesegments(child):
                yield n

    def __recursivetreesegments_uptodown(self, treesegment):
        #   treesegment : TreeSegment - Segment � retourner, ainsi que son parent (segment aval)
        #   retour de la m�thode : G�n�rateur de TreeSegment
        yield treesegment
        if not treesegment.is_root():
            for n in self.__recursivetreesegments_uptodown(treesegment.get_parent()):
                yield n

    def get_treesegment(self, id):
        #   id : int - Identifiant d'un segment
        #   retour de la m�thode : TreeSegment
        for segment in self.treesegments():
            if segment.id == id:
                return segment

    def leaves(self):
        #   retour de la m�thode : liste de Segments (les extr�mit�s amont)
        leaves = []
        for segment in self.treesegments():
            if segment.is_leaf():
                leaves.append(segment)
        return leaves

    def __str__(self):
        return str(self.treeroot)




    # def get_paths(self):
    #     paths = []
    #     for leaf in self.leaves():
    #         path = []
    #         reach = leaf
    #         path.append(reach)
    #         while not reach.is_root():
    #             reach = reach.parent
    #             path.append(reach)
    #         paths.append(path)
    #     return paths
