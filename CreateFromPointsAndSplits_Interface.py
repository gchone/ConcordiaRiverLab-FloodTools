# -*- coding: utf-8 -*-

#####################################################
# Guénolé Choné
# Date: 11 June 2021
# Description: Create From Points and Splits
#####################################################
import arcpy

from tree.TreeTools import *


class CreateFromPointsAndSplits(object):
    def __init__(self):
        self.label = "Create From Points and Splitting Points"
        self.description = "This tool creates two output layers with the from points and splitting points along routes"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param_network_shp = arcpy.Parameter(
            displayName="Network shapefile",
            name="network_shp",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_links_table = arcpy.Parameter(
            displayName="Links table",
            name="links_table",
            datatype="DEDbaseTable",
            parameterType="Required",
            direction="Input")
        param_RID_field = arcpy.Parameter(
            displayName="RID field",
            name="RID_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_points = arcpy.Parameter(
            displayName="From Points output",
            name="points",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")
        param_splits = arcpy.Parameter(
            displayName="Splitting points output",
            name="splits",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")

        param_RID_field.parameterDependencies = [param_network_shp.name]


        params = [param_network_shp, param_links_table, param_RID_field, param_points, param_splits]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        network_shp = parameters[0].valueAsText
        links_table = parameters[1].valueAsText
        RID_field = parameters[2].valueAsText
        points = parameters[3].valueAsText
        splits = parameters[4].valueAsText

        execute_CreateFromPointsAndSplits(network_shp, links_table, RID_field, points, splits)

        return
