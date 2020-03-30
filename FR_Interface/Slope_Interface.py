# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Mars 2017 - Création
# v1.1 - Juin 2018 - Séparation de l'interface et du métier
# v1.2 - Décembre 2018 - Ajout du workspace

import arcpy
from Slope import *


class pointflowpath:
   pass

class Slope(object):
    def __init__(self):

        self.label = "Pente"
        self.description = "Calcul la pente en suivant l'écoulement"
        self.canRunInBackground = False

    def getParameterInfo(self):

        param_dem = arcpy.Parameter(
            displayName="MNE",
            name="DEM",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
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
        param_distance = arcpy.Parameter(
            displayName="Distance de pente",
            name="distance",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param_slope = arcpy.Parameter(
            displayName="Pente",
            name="slope",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")
        param_newfp = arcpy.Parameter(
            displayName="Points de départ des pentes",
            name="newfp",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param0.filter.list = ["File System"]
        param0.value = arcpy.env.scratchWorkspace
        param_frompoint.filter.list = ["Point"]
        param_distance.value = 500

        params = [param_dem, param_flowdir, param_frompoint, param_distance, param_slope, param_newfp,param0]

        return params

    def isLicensed(self):

        return True

    def updateParameters(self, parameters):

        return

    def updateMessages(self, parameters):

        return

    def execute(self, parameters, messages):


        # Récupération des paramètres
        str_dem = parameters[0].valueAsText
        str_flowdir = parameters[1].valueAsText
        str_frompoint = parameters[2].valueAsText
        distancesmoothingpath = int(parameters[3].valueAsText)
        save_slope = parameters[4].valueAsText
        save_newfp = parameters[5].valueAsText
        arcpy.env.scratchWorkspace = parameters[6].valueAsText
        execute_Slope(arcpy.Raster(str_dem), arcpy.Raster(str_flowdir), str_frompoint, distancesmoothingpath, save_slope, save_newfp, messages)

        return