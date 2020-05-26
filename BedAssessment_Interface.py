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
from BedAssessment import *


class BedAssessment(object):
    def __init__(self):
        self.label = "�valuation du lit"
        self.description = "D�termine l'�l�vation de lit par mod�lisation 1D inverse"
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
        param_width = arcpy.Parameter(
            displayName="Largeur des cours d'eau",
            name="width",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_wssm = arcpy.Parameter(
            displayName="Surface de l'eau",
            name="wssm",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_manning = arcpy.Parameter(
            displayName="n de Manning dans le chenal",
            name="manning",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_Q = arcpy.Parameter(
            displayName="D�bit LiDAR",
            name="Q",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_slope = arcpy.Parameter(
            displayName="Pente � l'extr�mit� aval",
            name="downstream_s",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_bed = arcpy.Parameter(
            displayName="Output: ligne de l'�l�vation du lit (raster)",
            name="bed",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")
        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        param_manning.value = 0.03
        param_slope.value = 0.0001
        params = [param_flowdir, param_frompoint, param_width, param_wssm, param_manning, param_Q, param_slope, param_bed, param0]

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
        r_width = arcpy.Raster(parameters[2].valueAsText)
        r_zwater = arcpy.Raster(parameters[3].valueAsText)
        manning = float(parameters[4].valueAsText)
        r_Q = arcpy.Raster(parameters[5].valueAsText)
        downstream_s = float(parameters[6].valueAsText)
        result = parameters[7].valueAsText
        arcpy.env.scratchWorkspace = parameters[8].valueAsText

        execute_BedAssessment(r_flowdir, str_frompoint, r_width, r_zwater, manning, result, r_Q, downstream_s,
                              messages)
        return
