# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - June 2020 - Création.

import arcpy
from WSprofile import *


class WSprofile(object):
    def __init__(self):
        self.label = "Extraction de la surface de l'eau, méthode Info-CRUE 1"
        self.description = "Extraction de la surface de l'eau, méthode Info-CRUE 1"
        self.canRunInBackground = True

    def getParameterInfo(self):

        param_flowdir = arcpy.Parameter(
            displayName="Flow direction",
            name="flowdir",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_frompoint = arcpy.Parameter(
            displayName="Points de départ",
            name="frompoint",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_dem = arcpy.Parameter(
            displayName="DEM pour l'estimation de la surface de l'eau",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_ws = arcpy.Parameter(
            displayName="Output: ligne de la surface de l'eau (raster)",
            name="ws",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")
        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        params = [param_flowdir, param_frompoint, param_dem, param_ws, param0]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # Récupération des paramètres
        r_flowdir = arcpy.Raster(parameters[0].valueAsText)
        str_frompoint = parameters[1].valueAsText
        r_z = arcpy.Raster(parameters[2].valueAsText)
        str_ws = parameters[3].valueAsText
        arcpy.env.scratchWorkspace = parameters[4].valueAsText


        execute_WSprofile(r_flowdir, str_frompoint, r_z, str_ws, messages)

        return
