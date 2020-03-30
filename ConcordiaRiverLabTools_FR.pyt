# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Juin 2018 - Création

# Compilation des outils développés pour la gestion des rivières

from FR_Interface.FlowLength_Interface import *
from FR_Interface.Breach_Interface import *
from FR_Interface.Slope_Interface import *
from FR_Interface.CS_Interface import *
from FR_Interface.FloatEuclideanAllocation_Interface import *
from FR_Interface.LinearInterpolation_Interface import *
from FR_Interface.BridgeCorrection_Interface import *



class Toolbox(object):
    def __init__(self):

        self.label = "Outils de gestion des rivières"
        self.alias = ""



        self.tools = [FlowLength, Breach, Slope, CS, FloatEuclidean, LinearInterpolation, BridgeCorrection]



