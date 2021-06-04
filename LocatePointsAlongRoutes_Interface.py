# -*- coding: utf-8 -*-


#####################################################
# Mariana Liberman & Guénolé Choné
# Date:
# Description: Relate Networks
#####################################################


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
        param_routes = arcpy.Parameter(
            displayName="Network",
            name="routes",
            datatype="GPFeatureLayer",
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


        params = [param_points, param_routes, param_output, param_distance]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        execute_LocatePointsAlongRoutes(points, routes, output, distance)

        return
