# -*- coding: utf-8 -*-
import arcpy

from tree.TreeTools import *
from RelateNetworks import *
from LocatePointsAlongRoutes import *
from AssignPointToClosestPointOnRoute import *
from InterpolatePoints import *
from WSsmoothing import *

from numpy import genfromtxt

def execute_D8path(routes, links, RID_field, r_flow_dir, routeD8, linksD8, ptsonD8, relatetable, messages):
    fp = arcpy.CreateScratchName("fp", data_type="FeatureClass", workspace="in_memory")
    splits = arcpy.CreateScratchName("splits", data_type="FeatureClass", workspace="in_memory")
    execute_CreateFromPointsAndSplits(routes, links, RID_field, fp, splits)

    execute_TreeFromFlowDir(r_flow_dir, fp, routeD8, linksD8, RID_field, ptsonD8, messages, splits, 10000)

    execute_RelateNetworks(routes, RID_field, routeD8, RID_field, relatetable, messages)


def execute_OrderReaches(routes, links, RID_field, r_flowacc, routeD8, linksD8, ptsonD8, relatetable, outputfield, messages):

    D8_RID_field_in_relatetable = [f.name for f in arcpy.Describe(relatetable).fields][-2]

    # NB: extracting only the most points downstream points could have been avoided (as OrderTreeByFlowAcc use the most downstream point)
    # but maybe it's better that way as it avoid doing a costly convertion from table to shapefile and then ExtractMultiValuesToPoints
    QpointsD8 = arcpy.CreateScratchName("QptsD8", data_type="FeatureClass", workspace="in_memory")
    execute_LocateMostDownstreamPoints(routeD8, linksD8, RID_field, ptsonD8, "id", "RID", "dist", "X", "Y", QpointsD8)

    arcpy.sa.ExtractMultiValuesToPoints(QpointsD8, [[r_flowacc, "flowacc"]])

    arcpy.MakeFeatureLayer_management(QpointsD8, "qpts_lyr")
    arcpy.AddJoin_management("qpts_lyr", "id", ptsonD8, "id")
    arcpy.AddJoin_management("qpts_lyr", arcpy.Describe(ptsonD8).basename + ".RID", relatetable, D8_RID_field_in_relatetable)

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

def execute_ExtractDischarges(routes_Atlas, links_Atlas, RID_field_Atlas, routes_AtlasD8, links_AtlasD8, RID_field_AtlasD8, pts_D8, fpoints_atlas, routesD8, routeD8_RID, routes_main, route_main_RID, relate_table, r_flowacc, outpoints, messages):

    matchatlas = arcpy.CreateScratchName("matchatlas", data_type="ArcInfoTable", workspace="in_memory")
    execute_CheckNetFitFromUpStream(routes_AtlasD8, links_AtlasD8, RID_field_AtlasD8, routes_Atlas, links_Atlas, RID_field_Atlas,
                                    fpoints_atlas, matchatlas)

    QpointsD8 = arcpy.CreateScratchName("QptsD8", data_type="FeatureClass", workspace="in_memory")
    execute_LocateMostDownstreamPoints(routes_AtlasD8, links_AtlasD8, RID_field_AtlasD8, pts_D8, "id", "RID", "dist", "X", "Y", QpointsD8)

    Qpoints_subD8 = arcpy.CreateScratchName("QptsSub", data_type="ArcInfoTable", workspace="in_memory")
    arcpy.SpatialJoin_analysis(QpointsD8, routesD8, Qpoints_subD8, join_type="KEEP_COMMON")

    arcpy.sa.ExtractMultiValuesToPoints(Qpoints_subD8, [[r_flowacc, "flowacc"]])

    arcpy.MakeFeatureLayer_management(Qpoints_subD8, "qpts_lyr")
    arcpy.AddJoin_management("qpts_lyr", "id", pts_D8, "id")
    arcpy.AddJoin_management("qpts_lyr", arcpy.Describe(pts_D8).basename + "." + RID_field_AtlasD8, matchatlas,
                             RID_field_AtlasD8)

    D8_RID_field_in_relatetable = [f.name for f in arcpy.Describe(relate_table).fields][-2]
    arcpy.AddJoin_management("qpts_lyr", routeD8_RID, relate_table,
                             D8_RID_field_in_relatetable)


    # Numpy array conversion to keep only the relevant fields (Main route RID and RID from the Atlas)
    fields_to_keep = [arcpy.Describe(relate_table).basename + "." + route_main_RID]
    fields_to_keep.append(arcpy.Describe(matchatlas).basename + ".MATCH_ID")
    fields_to_keep.append(arcpy.Describe("qpts_lyr").basename + ".flowacc")
    fields_to_keep.append(arcpy.Describe(matchatlas).basename + ".TYPO")
    fields_to_keep.append(arcpy.Describe(matchatlas).basename + ".CLOSEST")
    fields_to_keep.append(arcpy.Describe(matchatlas).basename + ".SCORE")
    fields_to_keep.append("SHAPE@XY")
    nparray = arcpy.da.FeatureClassToNumPyArray("qpts_lyr", fields_to_keep)

    nparray.dtype.names = [route_main_RID, "MATCH_ID", "Flowacc", "TYPO", "CLOSEST", "SCORE", "XY"]

    Qpoints_subD8_bis = arcpy.CreateScratchName("QptsSub", data_type="FeatureClass", workspace="in_memory")
    arcpy.da.NumPyArrayToFeatureClass(nparray, Qpoints_subD8_bis, "XY", arcpy.Describe(routesD8).spatialReference)

    res_table = arcpy.CreateScratchName("QptsTable", data_type="ArcInfoTable", workspace="in_memory")
    execute_LocatePointsAlongRoutes(Qpoints_subD8_bis, route_main_RID, routes_main, route_main_RID, res_table, 10000)

    arcpy.AddField_management(res_table, "Drainage", "DOUBLE")
    arcpy.CalculateField_management(res_table, "Drainage", str(r_flowacc.meanCellWidth)+"*"+str(r_flowacc.meanCellHeight) + "*!Flowacc!/1000000.", "PYTHON")

    arcpy.MakeRouteEventLayer_lr(routes_main, route_main_RID, res_table, route_main_RID + " POINT MEAS", "res_lyr")

    arcpy.CopyFeatures_management("res_lyr", outpoints)

def execute_SpatializeQ(route_D8, RID_field_D8, D8pathpoints, r_flowacc, routes, links, RID_field, Qpoints, id_field_Qpoints, RID_Qpoints, dist_field_Qpoints, Drainage_field_Qpoints, Atlas_Drainage_field_Qpoints, AtlasReach_field_Qpoints, targetpoints, id_field_target, RID_field_target, Distance_field_target, DEM_field_target, Qcsv_file, output_points):

    # Extract Flow Acc along D8
    arcpy.MakeRouteEventLayer_lr(route_D8, RID_field_D8, D8pathpoints, RID_field_D8 + " POINT dist", "D8pts_lyr")
    D8pts = arcpy.CreateScratchName("targets", data_type="FeatureClass", workspace="in_memory")
    # I had a strange error when extracting the flow acc in a layer. Works if I use a Feature Class.... don't know why
    arcpy.CopyFeatures_management("D8pts_lyr", D8pts)
    arcpy.sa.ExtractMultiValuesToPoints(D8pts, [[r_flowacc, "flowacc"]])

    # Join target points with the closest D8 point with the same RID
    #targets_withFlowAcc = arcpy.CreateScratchName("targets", data_type="FeatureClass", workspace="in_memory")
    targets_withFlowAcc = r"E:\InfoCrue\Chaudiere\TestLinearRef\test.gdb\targets_withFlowAcc"
    execute_AssignPointToClosestPointOnRoute(D8pts, RID_field_D8, ["flowacc"], routes, RID_field, targetpoints, RID_field_target, Distance_field_target, targets_withFlowAcc)

    network = RiverNetwork()
    network.dict_attr_fields['id'] = RID_field
    network.load_data(routes, links)

    Qcollection = Points_collection(network, "Qpts")
    Qcollection.dict_attr_fields['id'] = id_field_Qpoints
    Qcollection.dict_attr_fields['reach_id'] = RID_Qpoints
    Qcollection.dict_attr_fields['dist'] = dist_field_Qpoints
    Qcollection.dict_attr_fields['FlowAccArea'] = Drainage_field_Qpoints
    Qcollection.dict_attr_fields['AtlasArea'] = Atlas_Drainage_field_Qpoints
    Qcollection.dict_attr_fields['AtlasID'] = AtlasReach_field_Qpoints
    Qcollection.load_table(Qpoints)

    targetcollection = Points_collection(network, "target")
    targetcollection.dict_attr_fields['id'] = id_field_target
    targetcollection.dict_attr_fields['reach_id'] = RID_field_target
    targetcollection.dict_attr_fields['dist'] = Distance_field_target
    targetcollection.dict_attr_fields['DEM'] = DEM_field_target
    targetcollection.dict_attr_fields['flowacc'] = "flowacc"
    targetcollection.load_table(targets_withFlowAcc)

    # First browse: assign the closest downstream Q point at each target point
    for reach in network.browse_reaches_down_to_up():
        if reach.is_downstream_end():
            lastQpts = None
        else:
            lastQpts = reach.get_downstream_reach().get_last_point(targetcollection).lastQpts
        for Qpts in reach.browse_points(Qcollection, orientation="DOWN_TO_UP"):
            if lastQpts is not None:
                if lastQpts.reach.id == reach.id:
                    min_dist = lastQpts.dist
                else:
                    min_dist = 0
                for targetpts in reach.browse_points(targetcollection, orientation="DOWN_TO_UP"):
                    if targetpts.dist >= min_dist and targetpts.dist < Qpts.dist:
                        targetpts.lastQpts = lastQpts
                        targetpts.lastQptsID = lastQpts.AtlasID # TEMP
            lastQpts = Qpts
        if lastQpts is not None:
            # Assign the lastQpts to target points until the end of the reach
            for targetpts in reach.browse_points(targetcollection, orientation="DOWN_TO_UP"):
                if targetpts.dist >= lastQpts.dist:
                    targetpts.lastQpts = lastQpts
                    targetpts.lastQptsID = lastQpts.AtlasID  # TEMP

    # First browse bis: assign the closest upstream Q point for points without downstream Q points
    for reach in network.browse_reaches_up_to_down():
        if reach.is_upstream_end():
            lastQpts = None
        for Qpts in reach.browse_points(Qcollection, orientation="UP_TO_DOWN"):
            if lastQpts is not None:
                for targetpts in reach.browse_points(targetcollection, orientation="UP_TO_DOWN"):
                    if not hasattr(targetpts, "lastQpts"):
                        targetpts.lastQpts = lastQpts
                        targetpts.lastQptsID = lastQpts.AtlasID  # TEMP


    # Second browse: Extract the right Q LiDAR discharge and do the drainage area correction
    Qdata_array = genfromtxt(Qcsv_file, delimiter=',')
    for reach in network.browse_reaches_down_to_up():
        for targetpts in reach.browse_points(targetcollection, orientation="DOWN_TO_UP"):
            #Qlidar = Qdata_array[targetpts.DEM][targetpts.lastQpts.AtlasID]
            #targetpts.Qlidar = Qlidar/lastQpts.AtlasArea*lastQpts.FlowAccArea
            pass

    # Save
    targetcollection.add_SavedVariable("lastQptsID", "lastQptsID")
    targetcollection.add_SavedVariable("flowacc", "flowacc")
    #targetcollection.add_SavedVariable("Qlidar", "Qlidar")
    targetcollection.save_points(output_points)