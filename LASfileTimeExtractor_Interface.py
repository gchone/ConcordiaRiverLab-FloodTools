# -*- coding: utf-8 -*-


#####################################################
# Guénolé Choné
# Description: Extract day of acquisition of LiDAR LAS files, create new LAS file for each day of acquisition
#####################################################

from LASfileTimeExtractor import *
import arcpy

class LASfileTimeExtractor(object):
    def __init__(self):
        self.label = "Create by-day LAS files"
        self.description = ""
        self.canRunInBackground = True

    def getParameterInfo(self):
        param_binlastoolsfolder = arcpy.Parameter(
            displayName="Lastools bin folder",
            name="binlastoolsfolder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param_lasfolder = arcpy.Parameter(
            displayName="Folder with LAS files",
            name="lasfolder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param_UTC = arcpy.Parameter(
            displayName="UTC zone",
            name="UTC",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_folderfilteredlas = arcpy.Parameter(
            displayName="Intermediary results folder - Original LAS files splitted by days",
            name="folderfilteredlas",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param_foldermergedlas = arcpy.Parameter(
            displayName="Final result folder - LAS files by days",
            name="foldermergedlas",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")


        params = [param_binlastoolsfolder, param_lasfolder, param_UTC, param_folderfilteredlas, param_foldermergedlas]


        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):

        str_binlastoolsfolder = parameters[0].valueAsText
        str_lasfolder = parameters[1].valueAsText
        UTC = parameters[2].valueAsText
        output_folder = parameters[3].valueAsText
        merge_folder = parameters[4].valueAsText

        execute_extract_bydays(str_binlastoolsfolder, str_lasfolder, UTC, output_folder, merge_folder, messages)
        return
