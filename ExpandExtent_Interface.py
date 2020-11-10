# coding: latin-1

#####################################################
# Gu�nol� Chon�
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - November 2020 - Cr�ation

import arcpy
from ExpandExtent import *


class ExpandExtent(object):
    def __init__(self):
        self.label = "Elargir �tendue du raster"
        self.description = "Ajoute une cellule � la taille du raster dans toutes les dimensions"
        self.canRunInBackground = True

    def getParameterInfo(self):

        param_raster = arcpy.Parameter(
            displayName="Input",
            name="raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_raster2 = arcpy.Parameter(
            displayName="Output",
            name="raster2",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Output")

        params = [param_raster, param_raster2]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # R�cup�ration des param�tres
        raster = arcpy.Raster(parameters[0].valueAsText)
        raster2 = parameters[1].valueAsText

        execute_ExpandExtent(raster, raster2, messages)

        return
