# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
# Fevrier 2019
#####################################################

# v1.1 - 10 mai 2018 - Correction des problèmes de zones dupliquées aux confluences (due aux segments d'un pixel de
#   long). Correction des longueurs des segments aux confluences.
# v1.2 - 28 février 2019 - Suppression des coupures aux confluences, ajout des coupures aux lacs.
# v1.3 - septembre 2019 - Coupure nette des rasters aux lacs + ajout du critère de pente
# v1.4 - octobre 2019 - Debug : problème de coupure des lacs avec multi fp, problème si zone de lac trop courte
# v1.5 - fevrier 2020 - Debug : problème de clip pour les confluent des segments coupé par les lacs
# v1.6 - mai 2020 - Coupure pour SUB et SUPER GC - Séparation interface et metier

import arcpy
from CreateZonesWlakesWSlope import *

class CreateZonesWlakes(object):
    def __init__(self):

        self.label = "Découpage en zones"
        self.description = "Découpage en zones"
        self.canRunInBackground = False

    def getParameterInfo(self):


        param_flowdir = arcpy.Parameter(
            displayName="Flow direction",
            name="flowdir",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param_lakes = arcpy.Parameter(
            displayName="Lacs et reservoirs",
            name="lakes",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_slope = arcpy.Parameter(
            displayName="Pente",
            name="slope",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_minslope = arcpy.Parameter(
            displayName="Pente minimale",
            name="minslope",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param_frompoint = arcpy.Parameter(
            displayName="Points de départ",
            name="frompoint",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_distance = arcpy.Parameter(
            displayName="Longueur des segments (m)",
            name="distance",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param_bufferw = arcpy.Parameter(
            displayName="Largeur minimale des zones (m)",
            name="bufferw",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param_typesim = arcpy.Parameter(
            displayName="Lignes des types de simulation",
            name="typesim",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_folder = arcpy.Parameter(
            displayName="Dossier pour les zones",
            name="folder ",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param0.filter.list = ["File System"]
        param0.value = arcpy.env.scratchWorkspace
        param_frompoint.filter.list = ["Point"]
        param_lakes.filter.list = ["POLYGON"]
        param_typesim.filter.list = ["Polyline"]
        param_distance.value = 15000
        param_bufferw.value = 3000
        param_minslope.value = 0.001

        params = [param_flowdir, param_lakes, param_slope, param_minslope, param_frompoint, param_distance, param_bufferw, param_typesim, param_folder, param0]

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
        str_lakes = parameters[1].valueAsText
        r_slope = arcpy.Raster(parameters[2].valueAsText)
        minslope = float(parameters[3].valueAsText)
        str_frompoint = parameters[4].valueAsText
        distance = int(parameters[5].valueAsText)
        bufferw = int(parameters[6].valueAsText)
        str_typesim = parameters[7].valueAsText
        str_folder = parameters[8].valueAsText

        arcpy.env.scratchWorkspace = parameters[9].valueAsText

        execute_CreateZone(r_flowdir, str_lakes, r_slope, minslope, str_frompoint, distance, bufferw, str_typesim, str_folder, messages)

        return





