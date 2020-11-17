# coding: latin-1

# Fichier TreeManager.py
# v0.0.2 - 24/10/2017

### Contenu ###
# classe TreeManager : Classe abstraite de gestion générique d'un arbre (méthodes d'intérogation sur l'ensemble de
#   l'arbre)

### Historique des versions ###
# v0.0.1 - 03/10/2017 - Création
# v0.0.2 - 24/10/2017 - Description modifiée - Guénolé Choné



class TreeManager(object):

    def __init__(self):
        self.treeroot = None

    def treesegments(self):
        #   retour de la méthode : Générateur de TreeSegment
        for n in self.__recursivetreesegments(self.treeroot):
            yield n

    def __recursivetreesegments(self, treesegment):
        #   treesegment : TreeSegment - Segment à retourner, ainsi que ces enfants (segments amont)
        #   retour de la méthode : Générateur de TreeSegment
        yield treesegment
        for child in treesegment.get_childrens():
            for n in self.__recursivetreesegments(child):
                yield n

    def get_treesegment(self, id):
        #   id : int - Identifiant d'un segment
        #   retour de la méthode : TreeSegment
        for segment in self.treesegments():
            if segment.id == id:
                return segment

    def leaves(self):
        #   retour de la méthode : liste de Segments (les extrémités amont)
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
