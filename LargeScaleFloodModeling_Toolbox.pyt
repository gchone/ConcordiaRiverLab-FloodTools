# -*- coding: utf-8 -*-

import arcpy


from RelateNetworks_Interface import *
from LocatePointsAlongRoutes_Interface import *
from LargeurParTransect_Interface import *
from DEMprocessing_Interface import *
from PlacePointsAlongReaches_Interface import *
from AssignPointToClosestPointOnRoute_Interface import *
from CreateTreeFromShapefile_Interface import *
from ChannelCorrection_Interface import *
from WSsmoothing_Interface import *
from TreeFromFlowDir_Interface import *
from CreateFromPointsAndSplits_Interface import *
from LocateMostDownstreamPoints_Interface import *
from FlowDirForWS_Interface import *
from InterpolatePoints_Interface import *
from DownstreamSlope_Interface import *
from BedAssessmentOld_Interface import *
from TopologicalD8RelateNetworks_Interface import *

class Toolbox(object):
    def __init__(self):

        self.label = "Tools for linear referencing"
        self.alias = ""

        self.tools = [TopologicalRelateNetworks, BedAssessmentIterations, DownstreamSlope, InterpolatePoints, FlowDirForWS, RelateNetworks, LocatePointsAlongRoutes, LargeurParTransect, BatchAggregate, PlacePointsAlongReaches, AssignPointToClosestPointOnRoute, CreateTreeFromShapefile, ChannelCorrection, WSsmoothing, TreeFromFlowDir, CreateFromPointsAndSplits, LocateMostDownstreamPoints]

