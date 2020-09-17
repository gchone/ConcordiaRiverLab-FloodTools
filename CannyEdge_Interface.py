# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Sept 2020 - Création.

import arcpy
from CannyEdge import *


class CannyEdge(object):
    def __init__(self):
        self.label = "Canny Edge Detection"
        self.description = "Application du filtre de Canny"
        self.canRunInBackground = True

    def getParameterInfo(self):

        param_raster = arcpy.Parameter(
            displayName="Pentes",
            name="slope",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_sigma = arcpy.Parameter(
            displayName="Sigma",
            name="sigma",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_threshold1 = arcpy.Parameter(
            displayName="Seuil bas",
            name="threshold1",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_threshold2 = arcpy.Parameter(
            displayName="Seuil haut",
            name="threshold2",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_edges = arcpy.Parameter(
            displayName="Output: arêtes",
            name="edges",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")
        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        params = [param_raster, param_sigma, param_threshold1, param_threshold2, param_edges, param0]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # Récupération des paramètres
        str_raster = parameters[0].valueAsText
        sigma = float(parameters[1].valueAsText)
        threshold1 = float(parameters[2].valueAsText)
        threshold2 = float(parameters[3].valueAsText)
        result = parameters[4].valueAsText
        arcpy.env.scratchWorkspace = parameters[5].valueAsText

        execute_CannyEdge(str_raster, sigma, threshold1, threshold2, result, messages)
        return
