# -*- coding: utf-8 -*-

import arcpy

from LASfileTimeExtractor_Interface import *
from RelateNetworks_Interface import *
from LocatePointsAlongRoutes_Interface import *
from LargeurParTransect_Interface import *
from DEMprocessing_Interface import *
from PlacePointsAlongReaches_Interface import *
from AssignPointToClosestPointOnRoute_Interface import *
from CreateTreeFromShapefile_Interface import *
from ChannelCorrection_Interface import *
#from WSsmoothing_Interface import *
from TreeFromFlowDir_Interface import *
from CreateFromPointsAndSplits_Interface import *
from LocateMostDownstreamPoints_Interface import *
from FlowDirForWS_Interface import *
from InterpolatePoints_Interface import *
from DownstreamSlope_Interface import *
from BedAssessmentOld_Interface import *
from TopologicalD8RelateNetworks_Interface import *
from CreateZones_Interface import *
from DefBci_Interface import *
from RunSim_Qlisted_Interface import *
from BridgeCorrection_Interface import *
from D8toD4_Interface import *

class Toolbox(object):
    def __init__(self):

        self.label = "Tools for linear referencing"
        self.alias = ""

        self.tools = [BridgeCorrection, D8toD4, RunSim_LISFLOOD, DefBciWithLateralWlakes_hdown, CreateZonesWlakes, LASfileTimeExtractor, TopologicalRelateNetworks, BedAssessmentIterations, DownstreamSlope, InterpolatePoints, FlowDirForWS, RelateNetworks, LocatePointsAlongRoutes, LargeurParTransect, BatchAggregate, PlacePointsAlongReaches, AssignPointToClosestPointOnRoute, CreateTreeFromShapefile, ChannelCorrection, TreeFromFlowDir, CreateFromPointsAndSplits, LocateMostDownstreamPoints]

