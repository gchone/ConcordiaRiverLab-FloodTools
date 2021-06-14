# -*- coding: utf-8 -*-


import arcpy
from tree.TreeTools import *
from RelateNetworks import *
from WidthAssessment import *
from WSsmoothing import *

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

    fpoints = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\from_points"
    splits = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\splits"
    #execute_CreateFromPointsAndSplits(routes, links, "RID", fpoints, splits)

    flowdir = arcpy.Raster(r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\DEM10m_avg_full_burned_flowdir")
    frompoints = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\from_points"
    routesD8 = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\routeD8"
    linksD8 =r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\linksD8"
    pathpoints = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\pathpointsD8"
    #execute_TreeFromFlowDir(flowdir, frompoints, routesD8, linksD8, "RID", pathpoints, messages)

    ### Water Surface ####
    flowdir_ws3m = arcpy.Raster(
        r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface.gdb\DEM3m_cor2_flowdir")
    routesD8_ws3m = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface.gdb\DEM3m_routeD8"
    linksD8_ws3m = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface.gdb\DEM3m_linksD8"
    pathpoints_ws3m = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface.gdb\DEM3m_pathpointsD8"
    #execute_TreeFromFlowDir(flowdir_ws3m, fpoints, routesD8_ws3m, linksD8_ws3m, "RID", pathpoints_ws3m, messages)

    datapoints = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface.gdb\datapoints"
    smoothedpts = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface.gdb\smoothedpts"
    execute_WSsmoothing(routesD8_ws3m, linksD8_ws3m, "RID", datapoints, "id", "RID", "dist", "offset", "X", "Y", "dem3mmin_br", "DEM3m_cor2_fill", smoothedpts)

    relate3m = r"E:\InfoCrue\Chaudiere\TestLinearRef\Watersurface.gdb\relate3m"
    execute_RelateNetworks(routes_main, "RID", routesD8_ws3m, "RID", relate3m, messages)




    ### Discharge ###
    atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Atlas_full2"
    route_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Atlas_routes"
    links_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Atlas_links"
    #execute_CreateTreeFromShapefile(atlas, route_atlas, links_atlas, "RID", "DownEnd", messages)
    fpoints_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Atlas_fp"
    splits_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\Atlas_splits"
    #execute_CreateFromPointsAndSplits(route_atlas, links_atlas, "RID", fpoints_atlas, splits_atlas)
    routesD8_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\routeD8_atlas"
    linksD8_atlas =r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\linksD8_atlas"
    pathpoints_atlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\pathpointsD8_atlas"
    #execute_TreeFromFlowDir(flowdir, fpoints_atlas, routesD8_atlas, linksD8_atlas, "RID", pathpoints_atlas, messages, splits_atlas, 10000)
    matchatlas = r"E:\InfoCrue\Chaudiere\TestLinearRef\Discharge\Discharge.gdb\match_nets"
    #execute_CheckNetFitFromUpStream(routesD8_atlas, linksD8_atlas, "RID", route_atlas, links_atlas, "RID", fpoints_atlas, matchatlas)

    QpointsD8 = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\QpointsD8"
    #execute_LocateMostDownstreamPoints(routesD8, linksD8, "RID", pathpoints, "id", "RID", "dist", "offset", "X", "Y", QpointsD8)

    basicnet_to_D8_linktable = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\net_to_D8_relationshiptable"
    #execute_RelateNetworks(routes_main, "RID", routesD8, "RID", basicnet_to_D8_linktable, messages)



    # Width postproc
    #widthdata = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\width_points_raw"
    #widthoutput = r"E:\InfoCrue\Chaudiere\TestLinearRef\New File Geodatabase.gdb\width_points_merge2"
    #execute_WidthPostProc(routes, "RID", "Main", links, widthdata, "CSid", "RID", "Distance_m", "Largeur_m", widthoutput, messages)