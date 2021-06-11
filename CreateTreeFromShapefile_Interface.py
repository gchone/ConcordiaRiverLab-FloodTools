# -*- coding: utf-8 -*-


#####################################################
# Guénolé Choné
# Date:
# Description: Create Tree from Shapefile
#####################################################

from tree.TreeTools import *

class CreateTreeFromShapefile(object):
    def __init__(self):
        self.label = "Create Tree from Shapefile"
        self.description = "This tool creates a river network data structure from a shapefile of lines"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param_rivernet = arcpy.Parameter(
            displayName="Input river shapefile",
            name="rivernet",
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
            datatype="GPTableView",
            parameterType="Required",
            direction="Output")
        param_routeID_field = arcpy.Parameter(
            displayName="Field containing the name of the reach ID field",
            name="routeID_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_downstream_reach_field = arcpy.Parameter(
            displayName="Name of the field identifying the most downstream reach",
            name="downstream_reach_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_channeltype_field = arcpy.Parameter(
            displayName="Field identifying the main or secondary channel",
            name="channeltype_field",
            datatype="Field",
            parameterType="Optional",
            direction="Input")


        param_routeID_field.parameterDependencies = [param_rivernet.name]
        param_downstream_reach_field.parameterDependencies = [param_rivernet.name]
        param_channeltype_field.parameterDependencies = [param_rivernet.name]

        params = [param_rivernet, param_route_shapefile, param_routelinks_table, param_routeID_field, param_downstream_reach_field, param_channeltype_field]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):

        rivernet = parameters[0].valueAsText
        route_shapefile = parameters[1].valueAsText
        routelinks_table = parameters[2].valueAsText
        routeID_field = parameters[3].valueAsText
        downstream_reach_field = parameters[4].valueAsText
        channeltype_field = parameters[5].valueAsText

        execute_CreateTreeFromShapefile(rivernet, route_shapefile, routelinks_table, routeID_field, downstream_reach_field, channeltype_field)

        return
