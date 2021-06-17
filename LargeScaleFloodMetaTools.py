# -*- coding: utf-8 -*-
import arcpy

from tree.TreeTools import *
from RelateNetworks import *
from LocatePointsAlongRoutes import *

def execute_OrderReaches(routes, links, RID_field, r_flow_dir, r_flowacc, outputfield, messages):


    fp = arcpy.CreateScratchName("fp", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
    splits = arcpy.CreateScratchName("splits", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
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
    execute_LocateMostDownstreamPoints(routeD8, linksD8, RID_field, ptsonD8, "id", "RID", "dist", "offset", "X", "Y", QpointsD8)

    arcpy.sa.ExtractMultiValuesToPoints(QpointsD8, [[r_flowacc, "flowacc"]])

    arcpy.MakeFeatureLayer_management(QpointsD8, "qpts_lyr")
    arcpy.AddJoin_management("qpts_lyr", "id", ptsonD8, "id")
    arcpy.AddJoin_management("qpts_lyr", arcpy.Describe(ptsonD8).basename + ".RID", relatetable, D8_RID_field_in_relatetable)

    arcpy.CopyFeatures_management("qpts_lyr", r"E:\InfoCrue\Chaudiere\TestLinearRef\test.gdb\qpts_lyr2")

    QpointsMain = arcpy.CreateScratchName("QptsMain", data_type="ArcInfoTable", workspace="in_memory")
    QpointsMain =  r"E:\InfoCrue\Chaudiere\TestLinearRef\test.gdb\QpointsMain3"
    execute_LocatePointsAlongRoutes("qpts_lyr", arcpy.Describe(relatetable).basename + "." + RID_field, routes, RID_field, QpointsMain, 10000)

    execute_OrderTreeByFlowAcc(routes, links, RID_field, QpointsMain, "id", "RID", "MEAS", "offset", "flowacc", outputfield)


