# -*- coding: utf-8 -*-

import arcpy


from RelateNetworks_Interface import *
from LocatePointsAlongRoutes_Interface import *
from LargeurParTransect_Interface import *
from DEMprocessing_Interface import *
from PlacePointsAlongReaches_Interface import *
from AssignPointToClosestPointOnRoute_Interface import *
from CreateTreeFromShapefile_Interface import *


class Toolbox(object):
    def __init__(self):

        self.label = "Tools for linear referencing"
        self.alias = ""

        self.tools = [RelateNetworks, LocatePointsAlongRoutes, LargeurParTransect, BatchAggregate, PlacePointsAlongReaches, AssignPointToClosestPointOnRoute, CreateTreeFromShapefile]
