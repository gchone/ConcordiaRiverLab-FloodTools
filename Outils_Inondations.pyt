# coding: latin-1


import arcpy

from CreateZonesWlakesWSlope import *
from DefBciWithLateral_lakes_hdown import *
from PrepaSim2DsupergcQvar_hdown import *
from RunSim2DsupergcQvar_hdown import *


class Toolbox(object):
    def __init__(self):

        self.label = "Outils inondations"
        self.alias = ""

        self.tools = [DefBciWithLateralWlakes_hdown, PrepaSim2DsupergcQvar_hdown, RunSim2DsupergcQvar_hdown, CreateZonesWlakes]



