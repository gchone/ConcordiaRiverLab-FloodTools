# -*- coding: utf-8 -*-

##################################################################
# Auteur: François Larouche-Tremblay, Ing, M Sc
# Description: Interface de la fonction LocaliserObstacles2D
##################################################################

# Versions:
# v1.0 - Sept 2019 - François Larouche-Tremblay - Creation
# v1.1 - May 2020 - Guénolé Choné - Brought into the FloodTools package.

import arcpy
from ChannelCorrection import *


class ChannelCorrection(object):
    def __init__(self):
        self.label = "Correction de la surface de l'eau"
        self.description = "Localise les obstacles sur la surface de l'eau et les supprime"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param_mnt = arcpy.Parameter(
            displayName="DEM",
            name="mnt",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_boundary = arcpy.Parameter(
            displayName="Transects perpendiculaires à l'écoulement aux extrémités amont et aval des cours d'eau",
            name="boundary",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_riverline = arcpy.Parameter(
            displayName="Ligne centrale des cours d'eau",
            name="riverline",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_riverbed = arcpy.Parameter(
            displayName="Polygone de la surface des cours d'eau",
            name="riverbed",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_breachedmnt = arcpy.Parameter(
            displayName="Output: Nom du raster contenant l'élévation corrigée de la surface de l'eau",
            name="breachedmnt",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")

        param_boundary.filter.list = ["Polyline"]
        param_riverbed.filter.list = ["Polygon"]
        param_riverline.filter.list = ["Polyline"]

        params = [param_mnt, param_boundary, param_riverbed, param_riverline, param_breachedmnt]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # Récupération des paramètres
        mnt = arcpy.Raster(parameters[0].valueAsText)
        boundary = parameters[1].valueAsText
        riverbed = parameters[2].valueAsText
        riverline = parameters[3].valueAsText
        breachedmnt = parameters[4].valueAsText

        execute_ChannelCorrection(mnt, boundary, riverbed, riverline, breachedmnt, messages)

        return
