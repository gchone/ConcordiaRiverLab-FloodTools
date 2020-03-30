# coding: latin-1

#####################################################
# Gu�nol� Chon�
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Juin 2018 - Cr�ation

# Compilation des outils d�velopp�s pour la gestion des rivi�res

from FR_Interface.FlowLength_Interface import *
from FR_Interface.Breach_Interface import *
from FR_Interface.Slope_Interface import *
from FR_Interface.CS_Interface import *
from FR_Interface.FloatEuclideanAllocation_Interface import *
from FR_Interface.LinearInterpolation_Interface import *
from FR_Interface.BridgeCorrection_Interface import *



class Toolbox(object):
    def __init__(self):

        self.label = "Outils de gestion des rivi�res"
        self.alias = ""



        self.tools = [FlowLength, Breach, Slope, CS, FloatEuclidean, LinearInterpolation, BridgeCorrection]



