# -*- coding: utf-8 -*-


#####################################################
# Guénolé Choné
# Date:
# Description: Spatialize Q floods
#####################################################

from LargeScaleFloodMetaTools import *

class SpatializeQflood_gauging_stations(object):
    def __init__(self):
        self.label = "Spatialize discharges from gauging stations - Flood discharge"
        self.description = ""
        self.canRunInBackground = True

    def getParameterInfo(self):

        param_r_flowacc = arcpy.Parameter(
            displayName="Flow Accumulation raster",
            name="r_flowacc",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_routes = arcpy.Parameter(
            displayName="Input route feature class (lines)",
            name="routes",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_links = arcpy.Parameter(
            displayName="Routes links",
            name="links",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")
        param_RID_field = arcpy.Parameter(
            displayName="RID field in routes feature class",
            name="RID_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_Qpoints = arcpy.Parameter(
            displayName="Qpoints",
            name="Qpoints",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")
        param_id_field_Qpoints = arcpy.Parameter(
            displayName="Id field in Qpoints",
            name="id_field_Qpoints",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_name_Qpoints = arcpy.Parameter(
            displayName="Gauging station name in Qpoints",
            name="name_Qpoints",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_drainage_Qpoints = arcpy.Parameter(
            displayName="Drainage area in Qpoints",
            name="drainage_Qpoints",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_RID_Qpoints = arcpy.Parameter(
            displayName="RID field in Qpoints",
            name="RID_Qpoints",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_dist_field_Qpoints = arcpy.Parameter(
            displayName="MEAS field in Qpoints ",
            name="dist_field_Qpoints",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_Q_field_Qpoints = arcpy.Parameter(
            displayName="Discharge field in Qpoints ",
            name="Q_field_Qpoints",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_targetpoints = arcpy.Parameter(
            displayName="Target points",
            name="targetpoints",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")
        param_id_field_target = arcpy.Parameter(
            displayName="ID field in target points feature class",
            name="id_field_target",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_RID_field_target = arcpy.Parameter(
            displayName="RID field in target points feature class",
            name="RID_field_target",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_Distance_field_target = arcpy.Parameter(
            displayName="MEAS field in target points feature class",
            name="Distance_field_target",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_beta = arcpy.Parameter(
            displayName="Beta coefficient",
            name="Beta",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_output_points = arcpy.Parameter(
            displayName="Points Output table",
            name="output_points",
            datatype="GPTableView",
            parameterType="Required",
            direction="Output")


        param_RID_field.parameterDependencies = [param_routes.name]
        param_id_field_Qpoints.parameterDependencies = [param_Qpoints.name]
        param_RID_Qpoints.parameterDependencies = [param_Qpoints.name]
        param_name_Qpoints.parameterDependencies = [param_Qpoints.name]
        param_drainage_Qpoints.parameterDependencies = [param_Qpoints.name]
        param_dist_field_Qpoints.parameterDependencies = [param_Qpoints.name]
        param_Q_field_Qpoints.parameterDependencies = [param_Qpoints.name]
        param_id_field_target.parameterDependencies = [param_targetpoints.name]
        param_RID_field_target.parameterDependencies = [param_targetpoints.name]
        param_Distance_field_target.parameterDependencies = [param_targetpoints.name]


        params = [param_r_flowacc, param_routes, param_links, param_RID_field, param_Qpoints, param_id_field_Qpoints, param_name_Qpoints, param_drainage_Qpoints, param_RID_Qpoints, param_dist_field_Qpoints, param_Q_field_Qpoints, param_targetpoints, param_id_field_target, param_RID_field_target, param_Distance_field_target, param_beta, param_output_points]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):

        r_flowacc = arcpy.Raster(parameters[0].valueAsText)
        routes = parameters[1].valueAsText
        links = parameters[2].valueAsText
        RID_field = parameters[3].valueAsText
        Qpoints = parameters[4].valueAsText
        id_field_Qpoints = parameters[5].valueAsText
        name_Qpoints = parameters[6].valueAsText
        drainage_Qpoints = parameters[7].valueAsText
        RID_Qpoints= parameters[8].valueAsText
        dist_field_Qpoints = parameters[9].valueAsText
        Q_field_Qpoints = parameters[10].valueAsText
        targetpoints = parameters[11].valueAsText
        id_field_target = parameters[12].valueAsText
        RID_field_target = parameters[13].valueAsText
        Distance_field_target = parameters[14].valueAsText
        beta_coef = float(parameters[15].valueAsText)
        output_points = parameters[16].valueAsText

        execute_SpatializeQ_from_gauging_stations(None, None, None, None, r_flowacc, routes,
                                                  links, RID_field, Qpoints, id_field_Qpoints, name_Qpoints,
                                                  drainage_Qpoints, RID_Qpoints, dist_field_Qpoints, Q_field_Qpoints,
                                                  targetpoints, id_field_target, RID_field_target,
                                                  Distance_field_target, None, None, beta_coef,
                                                  output_points, messages)

        return
