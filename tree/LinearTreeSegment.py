# coding: latin-1



### Historique des versions ###
# v1.0 - Nov 2020 - Création - Guénolé Choné



import tree.TreeSegment as TreeSegment



class LinearTreeSegment(TreeSegment.TreeSegment):

    ### Instance attributes ###
    # orientation: when using build_trees with a non-orientated network, flag for the orientation (True : good orientation)
    # length: total length of the reach

    def __init__(self, id):
        #   id : int - identifiant du segment
        TreeSegment.TreeSegment.__init__(self, id)


