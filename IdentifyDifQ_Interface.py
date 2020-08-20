# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Août 2020 - Création

import arcpy
from IdentifyDifQ import *


class IdentifyDifQ(object):
    def __init__(self):
        self.label = "Identifie les confluences de plus de X% d'augmentation d'aire drainée"
        self.description = "Identifie les confluences de plus de X% d'augmentation d'aire drainée"
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
        param_flowacc = arcpy.Parameter(
            displayName="Flow accumulation",
            name="flowacc",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_increase = arcpy.Parameter(
            displayName="Pourcentage d'augmentation de l'aire drainée",
            name="increase",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_pts = arcpy.Parameter(
            displayName="Points amont des confluences",
            name="ptsres",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        param_increase.value = 10
        params = [param_flowdir, param_frompoint, param_flowacc, param_increase, param_pts,param0]

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
        r_flowacc = arcpy.Raster(parameters[2].valueAsText)
        increase = float(parameters[3].valueAsText)/100.
        str_pts = parameters[4].valueAsText
        arcpy.env.scratchWorkspace = parameters[5].valueAsText


        execute_IdentifyDifQ(r_flowdir, str_frompoint, r_flowacc, increase, str_pts, messages)

        return
