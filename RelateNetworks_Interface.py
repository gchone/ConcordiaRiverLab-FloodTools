# -*- coding: utf-8 -*-


#####################################################
# Mariana Liberman & Guénolé Choné
# Date:
# Description: Relate Networks
#####################################################


from RelateNetworks import *

class RelateNetworks(object):
    def __init__(self):
        self.label = "Relate networks"
        self.description = "Relate two networks through a near table"
        self.canRunInBackground = True

    def getParameterInfo(self):

        param_shapefile_A = arcpy.Parameter(
            displayName="First Network",
            name="shapefile_A",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_RID_A = arcpy.Parameter(
            displayName="Route Field for First Network",
            name="RID_A",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_shapefile_B = arcpy.Parameter(
            displayName="Second network",
            name="shapefile_B",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_RID_B = arcpy.Parameter(
            displayName="Route Field for Second Network",
            name="RID_B",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_out_table = arcpy.Parameter(
            displayName="Output Table",
            name="out_table",
            datatype="DEDbaseTable",
            parameterType="Required",
            direction="Output")

        param_RID_A.parameterDependencies = [param_shapefile_A.name]
        param_RID_B.parameterDependencies = [param_shapefile_B.name]

        params = [param_shapefile_A, param_RID_A, param_shapefile_B, param_RID_B, param_out_table]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        shapefile_A = parameters[0].valueAsText
        RID_A = parameters[1].valueAsText
        shapefile_B = parameters[2].valueAsText
        RID_B = parameters[3].valueAsText
        out_table = parameters[4].valueAsText


        execute_RelateNetworks(shapefile_A, RID_A, shapefile_B, RID_B, out_table, messages)

        return
