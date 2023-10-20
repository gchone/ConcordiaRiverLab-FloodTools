# coding: latin-1

#####################################################
# Gu�nol� Chon�
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - May 2020 - Cr�ation.

import arcpy
from SpatializeQ_rasters import *


class SpatializeQ_rasters(object):
    def __init__(self):
        self.label = "Spatialisation des d�bits selon le D8"
        self.description = "Fournit des valeurs de d�bits le long des �coulements"
        self.canRunInBackground = True

    def getParameterInfo(self):

        param_flowdir = arcpy.Parameter(
            displayName="Flow direction",
            name="flowdir",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_frompoint = arcpy.Parameter(
            displayName="Points de d�part",
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
        param_q = arcpy.Parameter(
            displayName="D�bits ponctuels",
            name="q",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_interpolation = arcpy.Parameter(
            displayName="Interpolation entre les points de d�bits?",
            name="interpolation",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param_res = arcpy.Parameter(
            displayName="Output: lignes de d�bits (raster)",
            name="spatialq",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")

        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param_interpolation.value = False
        params = [param_flowdir, param_frompoint, param_flowacc, param_q, param_interpolation, param_res, param0]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # R�cup�ration des param�tres
        r_flowdir = arcpy.Raster(parameters[0].valueAsText)
        str_frompoint = parameters[1].valueAsText
        r_flowacc = arcpy.Raster(parameters[2].valueAsText)
        r_qpts = arcpy.Raster(parameters[3].valueAsText)
        interpolation = parameters[4].valueAsText == 'true'
        str_res = parameters[5].valueAsText
        arcpy.env.scratchWorkspace = parameters[6].valueAsText

        execute_SpatializeQ(r_flowdir, str_frompoint, r_flowacc, r_qpts, str_res, interpolation)

        return
