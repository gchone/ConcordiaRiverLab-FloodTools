# -*- coding: utf-8 -*-


import arcpy
from tree.TreeTools import *
from RelateNetworks import *
from WidthAssessment import *
from WSsmoothing import *
from AssignPointToClosestPointOnRoute import *
from InterpolatePoints import *
from ChannelCorrection import *

from LargeScaleFloodMetaTools import *

class Messages():
    def addErrorMessage(self, text):
        print (text)

    def addWarningMessage(self, text):
        print (text)

    def addMessage(self, text):
        print (text)




if __name__ == "__main__":
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True
    arcpy.env.scratchWorkspace = r"E:\InfoCrue\tmp"

    messages = Messages()

    # Create the river network
    shape = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\linear_net_d"
    routes = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\routes"
    links = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\routes_links"
    #execute_CreateTreeFromShapefile(shape, routes, links, "RID", "DownEnd", messages, "Main")
    shape_main = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\linear_main_d"
    routes_main = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\routes_main"
    links_main = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\routes_main_links"
    #execute_CreateTreeFromShapefile(shape_main, routes_main, links_main, "RID", "DownEnd", messages)


    flowdir = arcpy.Raster(
        r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\DEM10m_avg_full_burned_flowdir")

    routesD8 = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\routeD8"
    linksD8 =r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\linksD8"
    pathpoints = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\pathpointsD8"
    basicnet_to_D8_relatetable = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\net_to_D8_relationshiptable5"
    #execute_D8path(routes_main, links_main, "RID", flowdir, routesD8, linksD8, pathpoints, basicnet_to_D8_relatetable, messages)

    flowacc = arcpy.Raster(
        r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\DEM10m_avg_full_burned_flowacc")
    #execute_OrderReaches(routes_main, links_main, "RID", flowdir, flowacc, "Qorder2", messages)


    ### Water Surface ####
    lidar3m = arcpy.Raster(r"E:\InfoCrue\Chaudiere\TestLinearRef\WaterSurface2.gdb\dem3mmin_br_cor")
    channel = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\poly_chenal"
    ends = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface.gdb\Ends"
    linear = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\linear_main_d"
    DEMs_footprints = r"E:\InfoCrue\Chaudiere\Application_methodo_FLT_mars2021\DEM\Limites_single\Limites_merge.shp"
    DEMs_footprints_id = "ORIG_FID"
    ws3m = "E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface2.gdb\DEM3m_forws"
    #execute_ChannelCorrection(lidar3m, ends, channel, linear, DEMs_footprints, ws3m, messages)

    fpoints = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\from_points"
    # splits = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\splits"
    # execute_CreateFromPointsAndSplits(routes, links, "RID", fpoints, splits)

    flowdir_ws3m = arcpy.Raster(
        r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface2.gdb\dem3m_forws_flowdir")
    routesD8_ws3m = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface2.gdb\DEM3m_routeD8"
    linksD8_ws3m = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface2.gdb\DEM3m_linksD8"
    pathpoints_ws3m = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface2.gdb\DEM3m_pathpointsD8"
    #execute_TreeFromFlowDir(flowdir_ws3m, fpoints, routesD8_ws3m, linksD8_ws3m, "RID", pathpoints_ws3m, messages)

    lidar3m_forws = arcpy.Raster(r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface2.gdb\dem3m_forws")
    bathy_datapts = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface2.gdb\smoothedpts"

    #execute_ExtractWaterSurface(routes_main, links_main, "RID", "Qorder", routesD8_ws3m, "RID", "X", "Y", pathpoints_ws3m,
    #                            lidar3m, lidar3m_forws, 5, DEMs_footprints, DEMs_footprints_id, bathy_datapts, messages)



    ### Discharge ###
    atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Atlas_full2_corr"
    route_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Atlas_routes2"
    links_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Atlas_links2"
    #execute_CreateTreeFromShapefile(atlas, route_atlas, links_atlas, "RID", "DownEnd", messages)
    fpoints_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Atlas_fp2"
    splits_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Atlas_splits2"
    #execute_CreateFromPointsAndSplits(route_atlas, links_atlas, "RID", fpoints_atlas, splits_atlas)
    routesD8_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\routeD8_atlas2"
    linksD8_atlas =r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\linksD8_atlas2"
    pathpoints_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\pathpointsD8_atlas2"
    #execute_TreeFromFlowDir(flowdir, fpoints_atlas, routesD8_atlas, linksD8_atlas, "RID", pathpoints_atlas, messages, splits_atlas, 10000)

    Qpoints_match = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Qpoints_match"
    # execute_ExtractDischarges(route_atlas, links_atlas, "RID", routesD8_atlas, linksD8_atlas,
    #                               "RID", pathpoints_atlas, fpoints_atlas, routesD8, "RID", routes_main,
    #                               "RID", basicnet_to_D8_relatetable, flowacc, Qpoints_match, messages)

    Qpoints_match_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Qpoints_match_Atlas"
    Qcsv_file = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\qlidaratlas2020c.csv"
    Qpoints_spatialized = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Final_Qpoints"
    # execute_SpatializeQ(routesD8, "RID", pathpoints, basicnet_to_D8_relatetable, flowacc, routes_main, links_main, "RID", Qpoints_match_atlas, "OBJECTID", "RID", "MEAS",
    #                         "Sup_mod_km", "IDTRONCON",
    #                         bathy_datapts, "ObjectID_1", "RID", "MEAS", "ORIG_FID",
    #                         Qcsv_file, Qpoints_spatialized)

    #### Width assessment ####
    widthpts = r"E:\InfoCrue\Chaudiere\TestLinearRef\Width\Width.gdb\widthcalcpts"
    widthtransects = r"E:\InfoCrue\Chaudiere\TestLinearRef\Width\Width.gdb\widthtransects"
    execute_largeurpartransect(routes, "RID", channel, None, 1000, 5, widthtransects, widthpts, messages)

    #widthdata = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\width_points_raw"
    #widthoutput = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\width_points_merge2"
    #execute_WidthPostProc(routes, "RID", "Main", links, widthdata, "CSid", "RID", "Distance_m", "Largeur_m", widthoutput, messages)