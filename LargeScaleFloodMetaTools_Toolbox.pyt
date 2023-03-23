# -*- coding: utf-8 -*-

import arcpy


from OrderReaches_Interface import *
from ExtractWaterSurface_Interface import *
from FlowDirNetwork_Interface import *
from ExtractDischarges_Interface import *
from SpatializeQ_Interface import *
from WidthPostProc_Interface import *
from BedAssessment_Interface import *
from SpatializeQ_gauging_stations_Interface import *

class Toolbox(object):
    def __init__(self):

        self.label = "Metatools for linear referencing"
        self.alias = ""

        self.tools = [OrderReaches, ExtractWaterSurface, FlowDirNetwork, ExtractDischarges, SpatializeQ, WidthPostProc, BedAssessment, SpatializeQ_gauging_stations]

