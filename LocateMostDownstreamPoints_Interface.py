# -*- coding: utf-8 -*-

#####################################################
# Guénolé Choné
# Date: 11 June 2021
# Description: Locate Mos Downstream Points
#####################################################
import arcpy

from tree.TreeTools import *


class LocateMostDownstreamPoints(object):
    def __init__(self):
        self.label = "Locate Most Downstream Points"
        self.description = "This tool creates an output with the most downstream points of a network"
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
        param_datapoints = arcpy.Parameter(
            displayName="Datapoints",
            name="datapoints",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_id_field_pts = arcpy.Parameter(
            displayName="ID Field of points",
            name="id_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_RID_field_pts = arcpy.Parameter(
            displayName="RouteID Field of points",
            name="RID_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_Distance_field_pts = arcpy.Parameter(
            displayName="Distance field of points",
            name="Distance_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_offset_field_pts = arcpy.Parameter(
            displayName="Offset Field of points",
            name="offset_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_X_field_pts = arcpy.Parameter(
            displayName="X field of points",
            name="X_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_Y_field_pts = arcpy.Parameter(
            displayName="Y field of points",
            name="Y_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_output_pts = arcpy.Parameter(
            displayName="Output points",
            name="output_pts",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")

        param_RID_field.parameterDependencies = [param_network_shp.name]


        params = [param_network_shp, param_links_table, param_RID_field, param_datapoints, param_id_field_pts, param_RID_field_pts, param_Distance_field_pts, param_offset_field_pts, param_X_field_pts, param_Y_field_pts, param_output_pts]

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
        datapoints = parameters[3].valueAsText
        id_field_pts = parameters[4].valueAsText
        RID_field_pts = parameters[5].valueAsText
        Distance_field_pts = parameters[6].valueAsText
        offset_field_pts = parameters[7].valueAsText
        X_field_pts = parameters[8].valueAsText
        Y_field_pts = parameters[9].valueAsText
        output_pts = parameters[10].valueAsText

        execute_LocateMostDownstreamPoints(network_shp, links_table, RID_field, datapoints, id_field_pts, RID_field_pts, Distance_field_pts, offset_field_pts, X_field_pts, Y_field_pts, output_pts)

        return
