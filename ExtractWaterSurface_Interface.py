# -*- coding: utf-8 -*-


#####################################################
# Guénolé Choné
# Date:
# Description: Extract Water Surface
#####################################################

from LargeScaleFloodMetaTools import *

class ExtractWaterSurface(object):
    def __init__(self):
        self.label = "Extract Water Surface"
        self.description = ""
        self.canRunInBackground = True


    def getParameterInfo(self):
        param_routes = arcpy.Parameter(
            displayName="Input route feature class (lines)",
            name="routes",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_links = arcpy.Parameter(
            displayName="Input route link table",
            name="links",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")
        param_RID_field = arcpy.Parameter(
            displayName="RouteID field in the Input route feature class",
            name="RID_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_order_field = arcpy.Parameter(
            displayName="Order field in the Input route feature class (from 'Order reaches tool')",
            name="order_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_routes_3m = arcpy.Parameter(
            displayName="Input route 3m feature class (lines)",
            name="routes_3m",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_RID_field_3m = arcpy.Parameter(
            displayName="RouteID field in route 3m feature class",
            name="RID_field_3m",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_pts_table = arcpy.Parameter(
            displayName="Points table",
            name="pts_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Input")
        param_X_field_pts = arcpy.Parameter(
            displayName="Name of X field",
            name="X_field_pts",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_Y_field_pts = arcpy.Parameter(
            displayName="Name of Y field",
            name="Y_field_pts",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_lidar3m_cor = arcpy.Parameter(
            displayName="Lidar 3m cor",
            name="lidar3m_cor",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_lidar3m_forws = arcpy.Parameter(
            displayName="Lidar 3m forws",
            name="lidar3m_forws",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_interval = arcpy.Parameter(
            displayName="Interval in meters",
            name="interval",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_DEMs_footprints = arcpy.Parameter(
            displayName="DEMs footprint feature class",
            name="DEMs_footprints",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_DEMs_field = arcpy.Parameter(
            displayName="DEMs field in DEMs footprint feature class",
            name="DEMs_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_output_table = arcpy.Parameter(
            displayName="Output Points table",
            name="output_table",
            datatype="GPTableView",
            parameterType="Required",
            direction="Output")

        param_RID_field.parameterDependencies = [param_routes.name]
        param_order_field.parameterDependencies = [param_routes.name]
        param_RID_field_3m.parameterDependencies = [param_routes_3m.name]
        param_X_field_pts.parameterDependencies = [param_pts_table.name]
        param_Y_field_pts.parameterDependencies = [param_pts_table.name]
        param_DEMs_field.parameterDependencies = [param_DEMs_footprints.name]

        params = [param_routes, param_links, param_RID_field, param_order_field, param_routes_3m, param_RID_field_3m, param_X_field_pts, param_Y_field_pts, param_pts_table, param_lidar3m_cor, param_lidar3m_forws, param_interval, param_DEMs_footprints, param_DEMs_field, param_output_table]


        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):

        routes = parameters[0].valueAsText
        links = parameters[1].valueAsText
        RID_field = parameters[2].valueAsText
        order_field = parameters[3].valueAsText
        routes_3m = parameters[4].valueAsText
        RID_field_3m = parameters[5].valueAsText
        pts_table = parameters[6].valueAsText
        X_field_pts = parameters[7].valueAsText
        Y_field_pts = parameters[8].valueAsText
        lidar3m_cor = parameters[9].valueAsText
        lidar3m_forws = parameters[10].valueAsText
        interval = parameters[11].valueAsText
        DEMs_footprints = parameters[12].valueAsText
        DEMs_field = parameters[13].valueAsText
        ouput_table = parameters[14].valueAsText


        eexecute_ExtractWaterSurface(routes, links, RID_field, order_field, routes_3m, RID_field_3m, pts_table, X_field_pts,
                                    Y_field_pts, lidar3m_cor, lidar3m_forws, interval, DEMs_footprints,
                                    DEMs_field, ouput_table, messages)
        return
