# -*- coding: utf-8 -*-

### Historique des versions ###
# v2.0 - Fev 2020 - Création

from tree.NumpyArrayFedObject import *

class DataPoint(NumpyArrayFedObject):

    def __init__(self, id, downstream_point, reach, pointscollection):
        self.downstream_point = downstream_point
        self.id = id
        self.reach = reach
        self.pointscollection = pointscollection
        NumpyArrayFedObject.__init__(self, pointscollection)

