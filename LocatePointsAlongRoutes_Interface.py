# -*- coding: utf-8 -*-


#####################################################
# Mariana Liberman & Guénolé Choné
# Date:
# Description: Relate Networks
#####################################################
import arcpy

from LocatePointsAlongRoutes import *

class LocatePointsAlongRoutes(object):
    def __init__(self):
        self.label = "Locate Points Along Routes"
        self.description = "This tool creates an output table to project points to a network (based on linear " \
                           "referencing) after the RID of each point has been fixed using the Relate Networks tool."
        self.canRunInBackground = True

    def getParameterInfo(self):
        param_points = arcpy.Parameter(
            displayName="Points to project",
            name="points",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_points_RIDfield = arcpy.Parameter(
            displayName="RID field in Points layer",
            name="points_RIDfield",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_routes = arcpy.Parameter(
            displayName="Network",
            name="routes",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_routes_RIDfield = arcpy.Parameter(
            displayName="RID field in Routes layer",
            name="routes_RIDfield",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_output = arcpy.Parameter(
            displayName="Output table",
            name="output",
            datatype="DEDbaseTable",
            parameterType="Required",
            direction="Output")
        param_distance = arcpy.Parameter(
            displayName="Searching distance",
            name="distance",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")

        param_points_RIDfield.parameterDependencies = [param_points.name]
        param_routes_RIDfield.parameterDependencies = [param_routes.name]

        params = [param_points, param_points_RIDfield, param_routes, param_routes_RIDfield, param_output, param_distance]

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
        routes = parameters[2].valueAsText
        routes_RIDfield = parameters[3].valueAsText
        output = parameters[4].valueAsText
        distance = parameters[5].valueAsText

        execute_LocatePointsAlongRoutes(points, points_RIDfield, routes, routes_RIDfield, output, distance)

        return
