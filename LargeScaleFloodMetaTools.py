# -*- coding: utf-8 -*-
import arcpy

from tree.TreeTools import *
from RelateNetworks import *
from LocatePointsAlongRoutes import *
from AssignPointToClosestPointOnRoute import *
from InterpolatePoints import *
from WSsmoothing import *

def execute_OrderReaches(routes, links, RID_field, r_flow_dir, r_flowacc, outputfield, messages):


    fp = arcpy.CreateScratchName("fp", data_type="FeatureClass", workspace="in_memory")
    splits = arcpy.CreateScratchName("splits", data_type="FeatureClass", workspace="in_memory")
    execute_CreateFromPointsAndSplits(routes, links, RID_field, fp, splits)

    routeD8 = arcpy.CreateScratchName("routeD8", data_type="FeatureClass", workspace="in_memory")
    linksD8 = arcpy.CreateScratchName("linksD8", data_type="ArcInfoTable", workspace="in_memory")
    ptsonD8 = arcpy.CreateScratchName("ptsonD8", data_type="ArcInfoTable", workspace="in_memory")
    execute_TreeFromFlowDir(r_flow_dir, fp, routeD8, linksD8, RID_field, ptsonD8, messages, splits, 10000)
    #execute_TreeFromFlowDir(r_flow_dir, fp, routeD8, linksD8, RID_field, ptsonD8, messages)

    relatetable = arcpy.CreateScratchName("relatetable", data_type="ArcInfoTable", workspace="in_memory")
    execute_RelateNetworks(routes, RID_field, routeD8, RID_field, relatetable, messages)
    D8_RID_field_in_relatetable = [f.name for f in arcpy.Describe(relatetable).fields][-2]

    # NB: extracting only the most points downstream points could have been avoided (as OrderTreeByFlowAcc use the most downstream point)
    # but maybe it's better that way as it avoid doing a costly convertion from table to shapefile and then ExtractMultiValuesToPoints
    QpointsD8 = arcpy.CreateScratchName("QptsD8", data_type="FeatureClass", workspace="in_memory")
    execute_LocateMostDownstreamPoints(routeD8, linksD8, RID_field, ptsonD8, "id", "RID", "dist", "X", "Y", QpointsD8)

    arcpy.sa.ExtractMultiValuesToPoints(QpointsD8, [[r_flowacc, "flowacc"]])

    arcpy.MakeFeatureLayer_management(QpointsD8, "qpts_lyr")
    arcpy.AddJoin_management("qpts_lyr", "id", ptsonD8, "id")
    arcpy.AddJoin_management("qpts_lyr", arcpy.Describe(ptsonD8).basename + ".RID", relatetable, D8_RID_field_in_relatetable)

    arcpy.CopyFeatures_management("qpts_lyr", r"E:\InfoCrue\Chaudiere\TestLinearRef\test.gdb\qpts_lyr2")

    QpointsMain = arcpy.CreateScratchName("QptsMain", data_type="ArcInfoTable", workspace="in_memory")

    execute_LocatePointsAlongRoutes("qpts_lyr", arcpy.Describe(relatetable).basename + "." + RID_field, routes, RID_field, QpointsMain, 10000)

    execute_OrderTreeByFlowAcc(routes, links, RID_field, QpointsMain, "id", "RID", "MEAS", "flowacc", outputfield)

def execute_ExtractWaterSurface(routes, links, RID_field, order_field, routes_3m, RID_field_3m, X_field_pts, Y_field_pts, pts_table, lidar3m_cor, lidar3m_forws, interval, DEMs_footprints, DEMs_field, ouput_table, messages):

    relatetable = arcpy.CreateScratchName("relatetable", data_type="ArcInfoTable", workspace="in_memory")
    execute_RelateNetworks(routes, RID_field, routes_3m, RID_field_3m, relatetable, messages)
    RID3m_field_in_relatetable = [f.name for f in arcpy.Describe(relatetable).fields][-2]

    arcpy.MakeXYEventLayer_management (pts_table, X_field_pts, Y_field_pts, "pts_layer", routes_3m)
    arcpy.sa.ExtractMultiValuesToPoints("pts_layer", [lidar3m_cor, lidar3m_forws])

    arcpy.AddJoin_management("pts_layer", RID_field_3m, relatetable, RID3m_field_in_relatetable)

    pts_bathy = arcpy.CreateScratchName("pts_bathy", data_type="ArcInfoTable", workspace="in_memory")
    execute_PlacePointsAlongReaches(routes, links, RID_field, interval, pts_bathy)

    pts_bathy_withws = arcpy.CreateScratchName("pts_withws", data_type="ArcInfoTable", workspace="in_memory")

    lidar3m_cor_basename = arcpy.Describe(lidar3m_cor).basename
    lidar3m_forws_basename = arcpy.Describe(lidar3m_forws).basename
    execute_AssignPointToClosestPointOnRoute("pts_layer", arcpy.Describe(relatetable).basename + "." + RID_field, [lidar3m_cor_basename, lidar3m_forws_basename], routes, RID_field, pts_bathy, RID_field, "MEAS", pts_bathy_withws)

    pts_interpolated = arcpy.CreateScratchName("pts_interp", data_type="ArcInfoTable", workspace="in_memory")
    execute_InterpolatePoints(pts_bathy_withws, "ObjectID_1", RID_field, "MEAS", [lidar3m_cor_basename, lidar3m_forws_basename], pts_bathy, "ObjectID_1", RID_field, "MEAS", routes, links, RID_field, order_field, pts_interpolated)

    arcpy.MakeRouteEventLayer_lr(routes, RID_field, pts_interpolated, RID_field + " POINT MEAS", "interpolated_lyr")
    interpolated_withDEM = arcpy.CreateScratchName("interpDEM", data_type="FeatureClass", workspace="in_memory")
    arcpy.SpatialJoin_analysis("interpolated_lyr", DEMs_footprints, interpolated_withDEM)

    execute_WSsmoothing(routes, links, RID_field, interpolated_withDEM, "ObjectID_1", RID_field, "MEAS", lidar3m_cor_basename, lidar3m_forws_basename, DEMs_field, ouput_table)
