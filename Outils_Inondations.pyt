# coding: latin-1


import arcpy

from CreateZones_Interface import *
from DefBci_Interface import *
from RunSim_Interface import *
from ChannelCorrection_Interface import *
from WSsmoothing_Interface import *
from BedAssessment_Interface import *
from SpatializeQ_Interface import *

class Toolbox(object):
    def __init__(self):

        self.label = "Outils inondations"
        self.alias = ""

        self.tools = [DefBciWithLateralWlakes_hdown, RunSim2DsupergcQvar_hdown, CreateZonesWlakes, ChannelCorrection, WSsmoothing, BedAssessment, SpatializeQ]



