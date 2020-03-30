# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Juillet 2018 - Création
# v1.1 - Décembre 2018 - Ajout du workspace

import arcpy
from LinearInterpolation import *


class pointflowpath:
   pass

class LinearInterpolation(object):
    def __init__(self):

        self.label = "Interpolation lineaire"
        self.description = "Interpolation linéaire suivant l'écoulement"
        self.canRunInBackground = False

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
        param_values = arcpy.Parameter(
            displayName="Valeurs à interpoler",
            name="values",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")


        param_interpolatedbkf = arcpy.Parameter(
            displayName="Élévations interpolées",
            name="interpolated_values",
            datatype="DERasterDataset",
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

        params = [param_flowdir, param_frompoint, param_values, param_interpolatedbkf,param0]


        return params

    def isLicensed(self):

        return True

    def updateParameters(self, parameters):

        return

    def updateMessages(self, parameters):

        return

    def execute(self, parameters, messages):


        # Récupération des paramètres
        str_flowdir = parameters[0].valueAsText
        str_frompoint = parameters[1].valueAsText
        str_values = parameters[2].valueAsText
        SaveResult = parameters[3].valueAsText
        arcpy.env.scratchWorkspace = parameters[4].valueAsText
        execute_LinearInterpolation(arcpy.Raster(str_flowdir), str_frompoint, arcpy.Raster(str_values), SaveResult, messages)


        return