# -*- coding: utf-8 -*-


#####################################################
# Guénolé Choné
# Date: 10 June 2021
# Description: Assign points to the closest point on the Route
#####################################################
import arcpy

from AssignPointToClosestPointOnRoute import *

class AssignPointToClosestPointOnRoute(object):
    def __init__(self):
        self.label = "Project point to the closest point on the network"
        self.description = """This tool creates an output feature class  by projecting a point layer to the closest\
        point on a network. Both input layers (points and points on network) MUST have the RouteID field)."""

        self.canRunInBackground = True

    def getParameterInfo(self):
        param_points = arcpy.Parameter(
            displayName="Points layer to project",
            name="points",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_points_RIDfield = arcpy.Parameter(
            displayName="RouteID field in the points layer",
            name="points_RIDfield",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_points_onroute = arcpy.Parameter(
            displayName="Points layer on network",
            name="points_onroute",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_points_onroute_RIDfield = arcpy.Parameter(
            displayName="RouteID field in the points on network layer",
            name="points_onroute_RIDfield",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_output_shp = arcpy.Parameter(
            displayName="Output point layer",
            name="output_shp",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")


        param_points_RIDfield.parameterDependencies = [param_points.name]
        param_points_onroute_RIDfield.parameterDependencies = [param_points_onroute.name]

        params = [param_points, param_points_RIDfield, param_points_onroute, param_points_onroute_RIDfield, param_output_shp]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):

        points = parameters[0].valueAsText
        points_RIDfield = parameters[1].valueAsText
        points_onroute = parameters[2].valueAsText
        points_onroute_RIDfield = parameters[3].valueAsText
        output_shp = parameters[4].valueAsText


        execute_AssignPointToClosestPointOnRoute(points, points_RIDfield, points_onroute, points_onroute_RIDfield, output_shp)



        return