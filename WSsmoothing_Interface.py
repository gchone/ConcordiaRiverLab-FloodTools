# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - May 2020 - Création.

import arcpy
from WSsmoothing import *


class WSsmoothing(object):
    def __init__(self):
        self.label = "Extraction de la surface de l'eau avec lissage"
        self.description = "Effectue un lissage de la surface de l'eau"
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
        param_ws = arcpy.Parameter(
            displayName="DEM pour l'estimation de la surface de l'eau",
            name="ws",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_wserr = arcpy.Parameter(
            displayName="DEM pour l'estimation de l'erreur",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_smoothing = arcpy.Parameter(
            displayName="Paramètre de lissage",
            name="smoothing",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_wssm = arcpy.Parameter(
            displayName="Output: ligne de la surface de l'eau (raster)",
            name="wssm",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")
        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        param_smoothing.value = 0.9

        params = [param_flowdir, param_frompoint, param_ws, param_wserr, param_smoothing, param_wssm, param0]

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
        r_zerr = arcpy.Raster(parameters[3].valueAsText)
        smooth_perc = float(parameters[4].valueAsText)
        str_zwssm = parameters[5].valueAsText
        arcpy.env.scratchWorkspace = parameters[6].valueAsText


        execute_WSsmoothing(r_flowdir, str_frompoint, r_z, r_zerr, str_zwssm, smooth_perc)
        return
