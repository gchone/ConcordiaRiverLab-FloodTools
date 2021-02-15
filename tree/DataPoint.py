# -*- coding: utf-8 -*-

### Historique des versions ###
# v2.0 - Fev 2020 - Création

class DataPoint(object):

    def __init__(self, id, downstream_point, reach, distance, offset):
        self.downstream_point = downstream_point
        self.id = id
        self.reach = reach
        self.dist = distance
        self.offset = offset

