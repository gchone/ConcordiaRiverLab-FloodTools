# -*- coding: utf-8 -*-


#####################################################
# Guénolé Choné
# Date: 11 June 2021
# Description: Create Tree from Flow Direction raster
#####################################################

from tree.TreeTools import *

class TreeFromFlowDir(object):
    def __init__(self):
        self.label = "Create Tree from Flow Direction raster"
        self.description = "This tool creates a river network data structure from a Flow Direction raster"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param_r_flowdir = arcpy.Parameter(
            displayName="Flow direction raster",
            name="r_flowdir",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_str_frompoints = arcpy.Parameter(
            displayName="Point shapefile including the upstream ends of the network",
            name="str_frompoints",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_route_shapefile = arcpy.Parameter(
            displayName="Output river network shapefile",
            name="route_shapefile",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")
        param_routelinks_table = arcpy.Parameter(
            displayName="Output table providing the links between reaches",
            name="routelinks_table",
            datatype="DEDbaseTable",
            parameterType="Required",
            direction="Output")
        param_routeID_field = arcpy.Parameter(
            displayName="Field containing the name of the reach ID field",
            name="routeID_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_str_output_points = arcpy.Parameter(
            displayName="Output table of the Flow direction pixels along the flow path",
            name="str_output_points",
            datatype="DEDbaseTable",
            parameterType="Required",
            direction="Output")
        param_split_pts = arcpy.Parameter(
            displayName="Feature class containing the split points between lines",
            name="split_pts",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param_tolerance = arcpy.Parameter(
            displayName="Tolerance between split points and the network, in meters",
            name="tolerance",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input")

        #param_routeID_field.parameterDependencies = [param_route_shapefile.name]

        params = [param_r_flowdir, param_str_frompoints, param_route_shapefile, param_routelinks_table, param_routeID_field, param_str_output_points, param_split_pts, param_tolerance]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):

        r_flowdir = parameters[0].valueAsText
        str_frompoints = parameters[1].valueAsText
        route_shapefile = parameters[2].valueAsText
        routelinks_table = parameters[3].valueAsText
        routeID_field = parameters[4].valueAsText
        str_output_points = parameters[5].valueAsText
        split_pts = parameters[6].valueAsText
        tolerance = parameters[7].valueAsText


        execute_TreeFromFlowDir(r_flowdir, str_frompoints, route_shapefile, routelinks_table, routeID_field, str_output_points, split_pts, tolerance)
        return
