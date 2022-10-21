# -*- coding: utf-8 -*-
import arcpy
import numpy

from tree.TreeTools import *
from RelateNetworks import *
from LocatePointsAlongRoutes import *
from AssignPointToClosestPointOnRoute import *
from InterpolatePoints import *
from WSsmoothing import *
import ArcpyGarbageCollector as gc
from numpy.lib import recfunctions as rfn
import csv

def execute_FlowDirNetwork(routes, links, RID_field, r_flow_dir, routeD8, linksD8, ptsonD8, relatetable, messages):
    fp = gc.CreateScratchName("fp", data_type="FeatureClass", workspace="in_memory")
    splits = gc.CreateScratchName("splits", data_type="FeatureClass", workspace="in_memory")
    execute_CreateFromPointsAndSplits(routes, links, RID_field, fp, splits)

    execute_TreeFromFlowDir(r_flow_dir, fp, routeD8, linksD8, RID_field, ptsonD8, messages, splits, 10000)

    execute_RelateNetworks(routes, RID_field, routeD8, RID_field, relatetable, messages)


def execute_OrderReaches(routes, links, RID_field, r_flowacc, routeD8, linksD8, ptsonD8, relatetable, outputfield, messages):

    D8_RID_field_in_relatetable = [f.name for f in arcpy.Describe(relatetable).fields][-2]

    # NB: extracting only the most points downstream points could have been avoided (as OrderTreeByFlowAcc use the most downstream point)
    # but maybe it's better that way as it avoids doing a costly convertion from table to shapefile and then ExtractMultiValuesToPoints
    QpointsD8 = gc.CreateScratchName("QptsD8", data_type="FeatureClass", workspace="in_memory")
    execute_LocateMostDownstreamPoints(routeD8, linksD8, RID_field, ptsonD8, "id", "RID", "dist", "X", "Y", QpointsD8)

    arcpy.sa.ExtractMultiValuesToPoints(QpointsD8, [[r_flowacc, "flowacc"]])

    arcpy.MakeFeatureLayer_management(QpointsD8, "qpts_lyr")
    arcpy.AddJoin_management("qpts_lyr", "id", ptsonD8, "id")
    arcpy.AddJoin_management("qpts_lyr", arcpy.Describe(ptsonD8).basename + ".RID", relatetable, D8_RID_field_in_relatetable)

    QpointsMain = gc.CreateScratchName("QptsMain", data_type="ArcInfoTable", workspace="in_memory")

    execute_LocatePointsAlongRoutes("qpts_lyr", arcpy.Describe(relatetable).basename + "." + RID_field, routes, RID_field, QpointsMain, 10000)

    execute_OrderTreeByFlowAcc(routes, links, RID_field, QpointsMain, "id", "RID", "MEAS", "flowacc", outputfield)

def execute_ExtractWaterSurface(routes, links, RID_field, order_field, routes_3m, RID_field_3m, relatetable, pts_table, X_field_pts, Y_field_pts, lidar3m_cor, lidar3m_forws, DEMs_footprints, DEMs_field, pts_bathy, pts_bathy_ID_field, pts_bathy_RID_field, pts_bathy_dist_field, ouput_table, messages):
    # 2021-10-19 Assignation of elevation on points on routes (AssignPointToClosestPointOnRoute) done by "2-WAY CLOSEST" instead of "MEAN"
    #  relate table externalised, and inverted

    #relatetable = gc.CreateScratchName("relatetable", data_type="ArcInfoTable", workspace="in_memory")
    #execute_RelateNetworks(routes, RID_field, routes_3m, RID_field_3m, relatetable, messages)
    RID_field_in_relatetable = [f.name for f in arcpy.Describe(relatetable).fields][2]
    #RID3m_field_in_relatetable = [f.name for f in arcpy.Describe(relatetable).fields][-2]

    arcpy.MakeXYEventLayer_management (pts_table, X_field_pts, Y_field_pts, "pts_layer", routes_3m)
    arcpy.sa.ExtractMultiValuesToPoints("pts_layer", [lidar3m_cor, lidar3m_forws])

    arcpy.AddJoin_management("pts_layer", RID_field_3m, relatetable, RID_field_3m)

    pts_bathy_withws = gc.CreateScratchName("pts_withws", data_type="ArcInfoTable", workspace="in_memory")

    lidar3m_cor_basename = str(arcpy.Describe(lidar3m_cor).basename)
    lidar3m_forws_basename = str(arcpy.Describe(lidar3m_forws).basename)

    execute_AssignPointToClosestPointOnRoute("pts_layer", arcpy.Describe(relatetable).basename + "." + RID_field_in_relatetable, [lidar3m_cor_basename, lidar3m_forws_basename], routes, RID_field, pts_bathy, pts_bathy_RID_field, pts_bathy_dist_field, pts_bathy_withws, "2-WAY CLOSEST")
    pts_interpolated = gc.CreateScratchName("pts_interp", data_type="ArcInfoTable", workspace="in_memory")
    execute_InterpolatePoints(pts_bathy_withws, pts_bathy_ID_field, pts_bathy_RID_field, pts_bathy_dist_field, [lidar3m_cor_basename, lidar3m_forws_basename], pts_bathy, pts_bathy_ID_field, pts_bathy_RID_field, pts_bathy_dist_field, routes, links, RID_field, order_field, pts_interpolated)

    arcpy.MakeRouteEventLayer_lr(routes, RID_field, pts_interpolated, pts_bathy_RID_field + " POINT "+pts_bathy_dist_field, "interpolated_lyr")

    interpolated_withDEM = gc.CreateScratchName("interpDEM", data_type="FeatureClass", workspace="in_memory")
    arcpy.SpatialJoin_analysis("interpolated_lyr", DEMs_footprints, interpolated_withDEM)

    execute_WSsmoothing(routes, links, RID_field, order_field, interpolated_withDEM, pts_bathy_ID_field, pts_bathy_RID_field, pts_bathy_dist_field, lidar3m_cor_basename, lidar3m_forws_basename, DEMs_field, ouput_table)

def execute_ExtractDischarges(routes_Atlas, links_Atlas, RID_field_Atlas, routes_AtlasD8, links_AtlasD8, RID_field_AtlasD8, pts_D8, fpoints_atlas, routesD8, routeD8_RID, routes_main, route_main_RID, relate_table, r_flowacc, outpoints, messages):

    try:
        matchatlas = gc.CreateScratchName("matchatlas", data_type="ArcInfoTable", workspace="in_memory")
        execute_CheckNetFitFromUpStream(routes_AtlasD8, links_AtlasD8, RID_field_AtlasD8, routes_Atlas, links_Atlas, RID_field_Atlas,
                                        fpoints_atlas, matchatlas, messages, "ENDS")

        QpointsD8 = gc.CreateScratchName("QptsD8", data_type="FeatureClass", workspace="in_memory")
        execute_LocateMostDownstreamPoints(routes_AtlasD8, links_AtlasD8, RID_field_AtlasD8, pts_D8, "id", "RID", "dist", "X", "Y", QpointsD8)

        Qpoints_subD8 = gc.CreateScratchName("QptsSub", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
        # points should be on the lines, but sometimes there's is a more or less 1cm shift. So a tolerance (10cm) was added
        arcpy.SpatialJoin_analysis(QpointsD8, routesD8, Qpoints_subD8, join_type="KEEP_COMMON", search_radius=0.1)
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

        Qpoints_subD8_bis = gc.CreateScratchName("QptsSub", data_type="FeatureClass", workspace="in_memory")
        arcpy.da.NumPyArrayToFeatureClass(nparray, Qpoints_subD8_bis, "XY", arcpy.Describe(routesD8).spatialReference)

        res_table = gc.CreateScratchName("QptsTable", data_type="ArcInfoTable", workspace="in_memory")
        execute_LocatePointsAlongRoutes(Qpoints_subD8_bis, route_main_RID, routes_main, route_main_RID, res_table, 10000)

        arcpy.AddField_management(res_table, "Drainage", "DOUBLE")
        arcpy.CalculateField_management(res_table, "Drainage", str(r_flowacc.meanCellWidth)+"*"+str(r_flowacc.meanCellHeight) + "*!Flowacc!/1000000.", "PYTHON")

        arcpy.MakeRouteEventLayer_lr(routes_main, route_main_RID, res_table, route_main_RID + " POINT MEAS", "res_lyr")

        arcpy.CopyFeatures_management("res_lyr", outpoints)

    finally:
        gc.CleanAllTempFiles()


def execute_SpatializeQ(route_D8, RID_field_D8, D8pathpoints, relate_table, r_flowacc, routes, links, RID_field, Qpoints, id_field_Qpoints, RID_Qpoints, dist_field_Qpoints, AtlasReach_field_Qpoints, targetpoints, id_field_target, RID_field_target, Distance_field_target, DEM_field_target, Qcsv_file, output_points, messages):

    # Extract Flow Acc along D8
    arcpy.MakeRouteEventLayer_lr(route_D8, RID_field_D8, D8pathpoints, RID_field_D8 + " POINT dist", "D8pts_lyr")
    D8pts = gc.CreateScratchName("targets", data_type="FeatureClass", workspace="in_memory")
    # I had a strange error when extracting the flow acc in a layer. Works if I use a Feature Class.... I don't know why
    arcpy.CopyFeatures_management("D8pts_lyr", D8pts)
    arcpy.sa.ExtractMultiValuesToPoints(D8pts, [[r_flowacc, "flowacc"]])
    arcpy.MakeFeatureLayer_management(D8pts, "D8pts_lyr2")
    D8_RID_field_in_relatetable = [f.name for f in arcpy.Describe(relate_table).fields][-2]
    arcpy.AddJoin_management("D8pts_lyr2", RID_field_D8, relate_table,
                             D8_RID_field_in_relatetable)

    # Join target points with the closest D8 point with the same RID
    targets_withFlowAcc = gc.CreateScratchName("targets", data_type="FeatureClass", workspace="in_memory")
    execute_AssignPointToClosestPointOnRoute("D8pts_lyr2", arcpy.Describe(relate_table).basename + "." + RID_field, ["flowacc"], routes, RID_field, targetpoints, RID_field_target, Distance_field_target, targets_withFlowAcc, stat="CLOSEST")

    network = RiverNetwork()
    network.dict_attr_fields['id'] = RID_field
    network.load_data(routes, links)

    Qcollection = Points_collection(network, "Qpts")
    Qcollection.dict_attr_fields['id'] = id_field_Qpoints
    Qcollection.dict_attr_fields['reach_id'] = RID_Qpoints
    Qcollection.dict_attr_fields['dist'] = dist_field_Qpoints
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
        # Look for the closest downstream point in targetcollection
        down_point = None
        down_reach = reach
        while down_point is None and not down_reach.is_downstream_end():
            down_reach = down_reach.get_downstream_reach()
            down_point = down_reach.get_last_point(targetcollection)
        if reach.is_downstream_end():
            lastQpts = None
        else:
            # discharge point associated with the closest downstream point in targetcollection
            lastQpts = down_point.lastQpts
        # Is there a discharge point on the current reach?
        for Qpts in reach.browse_points(Qcollection, orientation="DOWN_TO_UP"):
            if lastQpts is not None:
                if lastQpts.reach.id == reach.id:
                    min_dist = lastQpts.dist
                else:
                    min_dist = 0
                for targetpt in reach.browse_points(targetcollection, orientation="DOWN_TO_UP"):
                    if targetpt.dist >= min_dist and targetpt.dist < Qpts.dist:
                        targetpt.lastQpts = lastQpts
                        targetpt.QptsID = lastQpts.AtlasID
            lastQpts = Qpts
        if lastQpts is not None:
            # Assign the lastQpts to target points until the end of the reach
            if lastQpts.reach.id == reach.id:
                min_dist = lastQpts.dist
            else:
                min_dist = 0
            for targetpt in reach.browse_points(targetcollection, orientation="DOWN_TO_UP"):
                if targetpt.dist >= min_dist:
                    targetpt.lastQpts = lastQpts
                    targetpt.QptsID = lastQpts.AtlasID

    # First browse bis: assign the closest upstream Q point for points without downstream Q points
    for reach in network.browse_reaches_up_to_down():
        if reach.is_upstream_end():
            lastQpts = None
        for Qpts in reach.browse_points(Qcollection, orientation="UP_TO_DOWN"):
            if lastQpts is not None:
                for targetpt in reach.browse_points(targetcollection, orientation="UP_TO_DOWN"):
                    if not hasattr(targetpt, "lastQpts"):
                        targetpt.lastQpts = lastQpts
                        targetpt.QptsID = lastQpts.AtlasID
            lastQpts = Qpts

    # Second browse: Extract the right Q LiDAR discharge and do the drainage area correction
    #  but first, the csv file is loaded into a dictionary
    #Qdata_array = genfromtxt(Qcsv_file, delimiter=',')
    Q_dict = {}
    with open(Qcsv_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        firstrowname = csvreader.fieldnames[0]
        for line in csvreader:
            Q_dict[line[firstrowname]]=line
    for reach in network.browse_reaches_down_to_up():
        for targetpt in reach.browse_points(targetcollection, orientation="DOWN_TO_UP"):
            try:
                Qlidar = float(Q_dict[str(targetpt.lastQpts.AtlasID)][str(targetpt.DEM)])
                targetpt.Qlidar = Qlidar * r_flowacc.meanCellWidth * r_flowacc.meanCellHeight *  targetpt.flowacc/1000000.
            except KeyError as e:
                messages.addErrorMessage("Missing line or column in the csv file: " + str(targetpt.DEM) + " / " + str(targetpt.lastQpts.AtlasID))

    # Originaly (commented below): Join the final results to the original target shapefile
    # Final thought: Better to leave this to be done manually
    targetcollection.add_SavedVariable("QptsID", "str", 20)
    targetcollection.add_SavedVariable("Qlidar", "float")

    #targets_withQ = gc.CreateScratchName("ttable", data_type="ArcInfoTable", workspace="in_memory")
    targetcollection.save_points(output_points)

    # # There was an issue with the Join. ArcGIS refused to mach the ID of the two tables. I don't get why.
    # # Resolved by using numpyarray
    # originalfields = [f.name for f in arcpy.Describe(targetpoints).fields]
    # original_nparray = arcpy.da.TableToNumPyArray(targetpoints, originalfields)
    # original_nparray = numpy.sort(original_nparray, order=id_field_target)
    # result_nparray = arcpy.da.TableToNumPyArray(targets_withQ, [id_field_target, "QptsID", "Qlidar"])
    # result_nparray = numpy.sort(result_nparray, order=id_field_target)
    # finalarray = rfn.merge_arrays([original_nparray, result_nparray[["QptsID", "Qlidar"]]], flatten=True)
    # if arcpy.env.overwriteOutput and arcpy.Exists(output_points):
    #     arcpy.Delete_management(output_points)
    # arcpy.da.NumPyArrayToTable(finalarray, output_points)

def execute_SpatializeQ_from_gauging_stations(route_D8, RID_field_D8, D8pathpoints, relate_table, r_flowacc, routes, links, RID_field, Qpoints, id_field_Qpoints, name_field_Qpoints, drainage_area_field_Qpoints, RID_Qpoints, dist_field_Qpoints, targetpoints, id_field_target, RID_field_target, Distance_field_target, DEM_field_target, Qcsv_file, beta_coef, output_points, messages):

    class Ref_point:
        def __init__(self, name, discharges, drainage_area, reach, dist):
            self.name = name
            self.discharges = discharges
            self.drainage_area = drainage_area
            self.reach = reach
            self.dist = dist

    # Extract Flow Acc along D8
    arcpy.MakeRouteEventLayer_lr(route_D8, RID_field_D8, D8pathpoints, RID_field_D8 + " POINT dist", "D8pts_lyr")
    D8pts = gc.CreateScratchName("targets", data_type="FeatureClass", workspace="in_memory")
    # I had a strange error when extracting the flow acc in a layer. Works if I use a Feature Class.... I don't know why
    arcpy.CopyFeatures_management("D8pts_lyr", D8pts)
    arcpy.sa.ExtractMultiValuesToPoints(D8pts, [[r_flowacc, "flowacc"]])

    arcpy.MakeFeatureLayer_management(D8pts, "D8pts_lyr2")
    D8_RID_field_in_relatetable = [f.name for f in arcpy.Describe(relate_table).fields][-2]
    arcpy.AddJoin_management("D8pts_lyr2", RID_field_D8, relate_table,
                             D8_RID_field_in_relatetable)

    # Join target points with the closest D8 point with the same RID
    targets_withFlowAcc = gc.CreateScratchName("targets", data_type="FeatureClass", workspace=r"in_memory")
    execute_AssignPointToClosestPointOnRoute("D8pts_lyr2", arcpy.Describe(relate_table).basename + "." + RID_field, ["flowacc"], routes, RID_field, targetpoints, RID_field_target, Distance_field_target, targets_withFlowAcc, stat="CLOSEST")

    network = RiverNetwork()
    network.dict_attr_fields['id'] = RID_field
    network.load_data(routes, links)

    Qcollection = Points_collection(network, "Qpts")
    Qcollection.dict_attr_fields['id'] = id_field_Qpoints
    Qcollection.dict_attr_fields['reach_id'] = RID_Qpoints
    Qcollection.dict_attr_fields['dist'] = dist_field_Qpoints
    Qcollection.dict_attr_fields['name'] = name_field_Qpoints
    Qcollection.dict_attr_fields['drainage_area'] = drainage_area_field_Qpoints
    Qcollection.load_table(Qpoints)

    targetcollection = Points_collection(network, "target")
    targetcollection.dict_attr_fields['id'] = id_field_target
    targetcollection.dict_attr_fields['reach_id'] = RID_field_target
    targetcollection.dict_attr_fields['dist'] = Distance_field_target
    targetcollection.dict_attr_fields['DEM'] = DEM_field_target
    targetcollection.dict_attr_fields['flowacc'] = "flowacc"
    targetcollection.load_table(targets_withFlowAcc)

    # Read the csv file, transpose it
    Q_dict = {} # dictionnary (key = name of gauging stations) with each entry being a dictionnary of discharges (key = code_dem)
    with open(Qcsv_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for station in csvreader.fieldnames[1:]:
            Q_dict[station] = {}
        firstrowname = csvreader.fieldnames[0]
        for line in csvreader:
            for station in csvreader.fieldnames[1:]:
                Q_dict[station][line[firstrowname]] = float(line[station])
    # For each gauging station point, assign its dictionnary of discharges
    for reach in network.browse_reaches_down_to_up():
        for Qpts in reach.browse_points(Qcollection, orientation="DOWN_TO_UP"):
            try:
                Qpts.discharges = Q_dict[Qpts.name]
            except KeyError as e:
                messages.addErrorMessage("Missing gauging station in the csv file: " + str(Qpts.name))


    # First browse: assign the upstream Q point(s) (in a list)
    for reach in network.browse_reaches_down_to_up():
        for targetpt in reach.browse_points(targetcollection, orientation="DOWN_TO_UP"):
            targetpt.upQpts = [] # just to initiate the lists
    for reach in network.browse_reaches_up_to_down():
        if reach.is_upstream_end():
            lastQpts = None
        for Qpts in reach.browse_points(Qcollection, orientation="UP_TO_DOWN"):
            if lastQpts is not None:
                if lastQpts.reach.id == reach.id:
                    max_dist = lastQpts.dist
                else:
                    max_dist = None
                for targetpt in reach.browse_points(targetcollection, orientation="UP_TO_DOWN"):
                    if (max_dist is None or targetpt.dist <= max_dist) and targetpt.dist > Qpts.dist:
                        if lastQpts.name not in [pt.name for pt in targetpt.upQpts]:
                            targetpt.upQpts.append(lastQpts)
            lastQpts = Ref_point(Qpts.name, Qpts.discharges, Qpts.drainage_area, Qpts.reach, Qpts.dist)

        if lastQpts is not None:
            # Assign the lastQpts to target points until the end of the reach
            if lastQpts.reach.id == reach.id:
                max_dist = lastQpts.dist
            else:
                max_dist = None
            for targetpt in reach.browse_points(targetcollection, orientation="UP_TO_DOWN"):
                if max_dist is None or targetpt.dist <= max_dist:
                    if lastQpts.name not in [pt.name for pt in targetpt.upQpts]:
                        targetpt.upQpts.append(lastQpts)


    # Second browse: assign the closest downstream Q point at each target point
    # In the same browse, compute the discharges, by linear interpolation between each upstream/downstream pairs
    # If there are several upstream points, weight the results according to the upstream points drainage area
    # The final upstream point of a reach act as an input Q point for the upstream reaches
    for reach in network.browse_reaches_down_to_up():

        ### First block : find the closest downstream Q point ###

        lastQpts = None
        if not reach.is_downstream_end():
            lastQpts = reach.get_downstream_reach().upstream_calculated_Q

        # Is there a discharge point on the current reach?
        for Qpts in reach.browse_points(Qcollection, orientation="DOWN_TO_UP"):
            if lastQpts is not None:
                if lastQpts.reach.id == reach.id:
                    min_dist = lastQpts.dist
                else:
                    min_dist = 0
                for targetpt in reach.browse_points(targetcollection, orientation="DOWN_TO_UP"):
                    if targetpt.dist >= min_dist:
                        targetpt.downQpts = lastQpts
            lastQpts = Ref_point(Qpts.name, Qpts.discharges, Qpts.drainage_area, Qpts.reach, Qpts.dist)

        if lastQpts is not None:
            # Assign the lastQpts to target points until the end of the reach
            if lastQpts.reach.id == reach.id:
                min_dist = lastQpts.dist
            else:
                min_dist = 0
            for targetpt in reach.browse_points(targetcollection, orientation="DOWN_TO_UP"):
                if targetpt.dist >= min_dist:
                    targetpt.downQpts = lastQpts


        ### Second block : compute the discharges ###

        for targetpt in reach.browse_points(targetcollection, orientation="DOWN_TO_UP"):

            localarea = targetpt.flowacc*r_flowacc.meanCellWidth*r_flowacc.meanCellHeight/1000000.
            if not hasattr(targetpt, "downQpts"): # there is no downstream point
                # A simple proportionnality of A**beta is done for each upstream point
                for uppt in targetpt.upQpts:
                    uppt.interpolatedQ = {Qupkey:uppt.discharges[Qupkey]*(localarea/uppt.drainage_area)**beta_coef for Qupkey in uppt.discharges}
            else:
                # Linear interpolation of A**beta
                for uppt in targetpt.upQpts:
                    Q_from_down = {Qdownkey:(localarea ** beta_coef - uppt.drainage_area ** beta_coef) / (
                                targetpt.downQpts.drainage_area ** beta_coef - uppt.drainage_area ** beta_coef)*targetpt.downQpts.discharges[Qdownkey] for Qdownkey in targetpt.downQpts.discharges}
                    Q_from_up = {Qupkey:(targetpt.downQpts.drainage_area ** beta_coef - localarea ** beta_coef) / (
                                targetpt.downQpts.drainage_area ** beta_coef - uppt.drainage_area ** beta_coef)*uppt.discharges[Qupkey] for Qupkey in uppt.discharges}

                    uppt.interpolatedQ = {Qdownkey:Q_from_down[Qdownkey] + Q_from_up[Qdownkey] for Qdownkey in targetpt.downQpts.discharges}

            # weight the results according to the upstream points drainage area
            if len(targetpt.upQpts)>0:
                targetpt.weightedQ = {Qupkey:0 for Qupkey in targetpt.upQpts[0].discharges}
                totalweight = sum([uppt.drainage_area for uppt in targetpt.upQpts])
                for uppt in targetpt.upQpts:
                    targetpt.weightedQ = {Qupkey:targetpt.weightedQ[Qupkey] + uppt.interpolatedQ[Qupkey]*uppt.drainage_area/totalweight for Qupkey in uppt.discharges}
            else: # there is no upstream points
                if hasattr(targetpt, "downQpts"): # there is a downstream point
                    # A simple proportionnality of A**beta is done from the downstream point
                    targetpt.weightedQ = {
                        Qdownkey: targetpt.downQpts.discharges[Qdownkey] * (localarea / targetpt.downQpts.drainage_area) ** beta_coef for Qdownkey in targetpt.downQpts.discharges}

            # Export the discharge corresponding to the local day (local DEM) (it needs to be an attribute)
            if hasattr(targetpt, "weightedQ"):
                targetpt.computedQLiDAR = targetpt.weightedQ[targetpt.DEM]
            else:
                targetpt.computedQLiDAR = -999


        ### Third block : Convert the final upstream point into an Q input ###
        lastuppt = reach.get_last_point(targetcollection)
        reach.upstream_calculated_Q = Ref_point("uppt_reach"+str(reach.id), lastuppt.weightedQ,
                                                lastuppt.flowacc*r_flowacc.meanCellWidth*r_flowacc.meanCellHeight/1000000.,
                                                reach, lastuppt.dist)


    targetcollection.add_SavedVariable("computedQLiDAR", "float")
    targetcollection.save_points(output_points)



