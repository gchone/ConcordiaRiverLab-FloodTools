# -*- coding: utf-8 -*-

import arcpy


from RelateNetworks_Interface import *
from LocatePointsAlongRoutes_Interface import *


class Toolbox(object):
    def __init__(self):

        self.label = "Tools for linear referencing"
        self.alias = ""

        self.tools = [RelateNetworks, LocatePointsAlongRoutes]
