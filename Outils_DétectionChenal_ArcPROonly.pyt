# coding: latin-1


import arcpy


from ChannelDetection_Interface import *
from CannyEdge_Interface import *
from RiverPolygon_Interface import *

class Toolbox(object):
    def __init__(self):

        self.label = "Outils pour la détection du chenal"
        self.alias = ""

        self.tools = [ChannelDetection, CannyEdge, RiverPolygon]



