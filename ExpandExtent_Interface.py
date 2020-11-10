# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - November 2020 - Création

import arcpy
from ExpandExtent import *


class ExpandExtent(object):
    def __init__(self):
        self.label = "Elargir étendue du raster"
        self.description = "Ajoute une cellule à la taille du raster dans toutes les dimensions"
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
        # Récupération des paramètres
        raster = arcpy.Raster(parameters[0].valueAsText)
        raster2 = parameters[1].valueAsText

        execute_ExpandExtent(raster, raster2, messages)

        return
