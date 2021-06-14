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
        self.label = "Locate most downstream points on network"
        self.description = "This tool creates an output point layer with the most downstream points of a network"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param_network_shp = arcpy.Parameter(
            displayName="Network layer",
            name="network_shp",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_links_table = arcpy.Parameter(
            displayName="Link table",
            name="links_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")
        param_RID_field = arcpy.Parameter(
            displayName="RouteID field in the network layer",
            name="RID_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_datapoints = arcpy.Parameter(
            displayName="Flow direction pixels along flow path table",
            name="datapoints",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")
        param_id_field_pts = arcpy.Parameter(
            displayName="ID Field name for point layer",
            name="id_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_RID_field_pts = arcpy.Parameter(
            displayName="RouteID field name for point layer",
            name="RID_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_Distance_field_pts = arcpy.Parameter(
            displayName="Name for distance field of point layer",
            name="Distance_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_offset_field_pts = arcpy.Parameter(
            displayName="Name for offset field of point layer",
            name="offset_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_X_field_pts = arcpy.Parameter(
            displayName="Name for X field of point layer",
            name="X_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_Y_field_pts = arcpy.Parameter(
            displayName="Name for Y field of point layer",
            name="Y_field_pts",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_output_pts = arcpy.Parameter(
            displayName="Output point layer",
            name="output_pts",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")

        param_RID_field.parameterDependencies = [param_network_shp.name]
        param_id_field_pts.value = "ID"
        param_RID_field_pts.value = "RID"
        param_Distance_field_pts.value = "dist"
        param_offset_field_pts.value = "offset"
        param_X_field_pts.value = "X"
        param_Y_field_pts.value = "Y"


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
