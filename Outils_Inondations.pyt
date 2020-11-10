# coding: latin-1


import arcpy

from CreateZones_Interface import *
from DefBci_Interface import *
from RunSim_Interface import *
from ChannelCorrection_Interface import *
from WSsmoothing_Interface import *
from BedAssessment_Interface import *
from SpatializeQ_Interface import *
from ChannelDetection_Interface import *
from WSprofile_Interface import *
from RunSim_prevision_Interface import *
from IdentifyDifQ_Interface import *
from RunSim_prevision_2var_Interface import *
from ExpandExtent_Interface import *

class Toolbox(object):
    def __init__(self):

        self.label = "Outils inondations"
        self.alias = ""

        self.tools = [ExpandExtent, DefBciWithLateralWlakes_hdown, RunSim2DsupergcQvar_hdown, CreateZonesWlakes, ChannelCorrection, WSsmoothing, BedAssessment, SpatializeQ, ChannelDetection, WSprofile, RunSim2D_prevision, IdentifyDifQ, RunSim2D_prevision_2var]



