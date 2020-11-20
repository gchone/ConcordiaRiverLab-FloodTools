# -*- coding: utf-8 -*-


#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Post-processing the velocity output of LISFLOOD-FP
# Compute velocity results at the original DEM pixel location, for both channel (1D) and floodplain (2D) results
# - Simulations must be run with the "Qoutput" keywords
# - Use the last results (when there are several results at different time saved by the "saveint" keyword). It should ideally be the
#    steady flow results ("-9999" results).
# - This script is made to be used with the results of the tiling process and elevation post-processing of the "RunSim2D"
#   scripts. Velocities are merged together form the different tiles (with the same priority than the one used for the
#   flood water surface elevation
# - Outputs are:
#   * vx : X-axis component of the velocity, in the floodplain
#   * xy : Y-axis component of the velocity, in the floodplain
#   * v_channel : norm of the velocity vector in the channel (no indication of the direction)

# Notes about velocity output with LISFLOOD-FP (version 7.0.6)
# - Two keywords can output velocities: "hazard" and "Voutput"
# - "hazard" output signed velocities in the 2D domain, for results at timestep (e.g. -0001) and for steady flow (-9999)
#   results. It also output max results (in absolute values). There are no results in the 1D domain (channel centerline)
# - "Voutput" seems bugged, as all velocity results are 0
# - "Qoutput" doesn't output velocities, but discharges between cells. It can be easily converted into velocities. It
#   provides results for the 1D domains (files .Qcx and Qcy) or for both 1D and 2D domains (files .Qx and .Qy). This
#   script uses theses results to compute the velocities.
#
# All V and Q outputs from LISFLOOD-FP are rasters, providing information for the interface between two original (DEM)
#   cells. Consequently, the V and Q rasters are shifted of half a cell-size in one direction (so the V and Q cells
#   center is at the interface between two original DEM cells). This script compute the average velocities at the
#   original DEM cells positions.
#



# Versions
# v1.0 - Nov 2020 - Création

import arcpy
import os
import glob



def conversion(folder):


        # Get all the results in the folder
        globres = glob.glob(os.path.join(folder, "res", "*.Qx"))

        # List the differents simulations in the folder
        list_zones = set(f[:-8] for f in globres)


        for zone in list_zones:
            # For each simulation, get the list of results (i.e. [9999, 0001, 0000])
            print zone
            list_res_num = sorted([x[-7:-3] for x in globres if x.startswith(zone)], reverse=True)
            print list_res_num
            if len(list_res_num) > 0:
                # Take the fist result of the list and rename the file with a .asc extension
                os.rename(zone + "-" + list_res_num[0] + ".Qx", zone + "_Qx.asc")
                os.rename(zone + "-" + list_res_num[0] + ".Qy", zone + "_Qy.asc")
        return list_zones

def postproc_v(width, bed, dem, res_folder):

    result = arcpy.Raster(os.path.join(res_folder, "lisflood_res"))

    arcpy.env.workspace = res_folder


    elev_rasters = arcpy.ListRasters("elev_zone*")
    Vx_rasters = []
    Vy_rasters = []
    Vch_rasters = []
    tmp_elev_rasters = []
    # Loop to create lists of the qx, qy and elevation raster (with -9999 instead of NoData) results
    for elev_raster in elev_rasters:
        # create a temp version of elev_zone* by replacing NoData by -9999 for the full extent
        # (used latter for the HighestPosition / Pick process
        with arcpy.EnvManager(extent=result):
            tmp_elev_raster = arcpy.sa.Con(arcpy.sa.IsNull(elev_raster) == 1, -9999, elev_raster)
        tmp_elev_raster.save(os.path.join(arcpy.env.scratchWorkspace, "tmp_e_"+elev_raster[5:]))
        tmp_elev_rasters.append(os.path.join(arcpy.env.scratchWorkspace, "tmp_e_"+elev_raster[5:]))
        qx_raster = os.path.join(res_folder, "res", elev_raster[5:] + "_Qx.asc")
        qy_raster = os.path.join(res_folder, "res", elev_raster[5:] + "_Qy.asc")
        print elev_raster[5:]
        ### Computing the velocity
        # replace NoData by 0 (so the mean is than correctly computed)
        qx_raster = arcpy.sa.Con(arcpy.sa.IsNull(qx_raster) == 1, 0, qx_raster)
        qy_raster = arcpy.sa.Con(arcpy.sa.IsNull(qy_raster) == 1, 0, qy_raster)
        # The average of both cells (2 cells horizontally for qx, 2 vertically for qy) must be taken
        # Focal Statistics with a 1x2 (or 2x1) compute the average. The results are than shifted to snap the elevation raster
        # NbrRectangle(2,1) take the original cell and its right one, so the shift is to the right (positive)
        # NbrRectangle(1,2) take the original cell and its bottom one, so the shift is downward (negative)
        mean = arcpy.sa.FocalStatistics(qx_raster, arcpy.sa.NbrRectangle(2,1, "CELL"), "MEAN", "NODATA")
        arcpy.Shift_management(mean, os.path.join(arcpy.env.scratchWorkspace, "qxmean"), qx_raster.meanCellWidth/2., 0, result)
        mean = arcpy.sa.FocalStatistics(qy_raster, arcpy.sa.NbrRectangle(1, 2, "CELL"), "MEAN", "NODATA")
        arcpy.Shift_management(mean, os.path.join(arcpy.env.scratchWorkspace, "qymean"), 0, -qy_raster.meanCellHeight / 2., result)
        arcpy.DefineProjection_management(os.path.join(arcpy.env.scratchWorkspace, "qxmean"), bed)
        arcpy.DefineProjection_management(os.path.join(arcpy.env.scratchWorkspace, "qymean"), bed)

        # converting the q in v in the channel
        area = (result - bed)*width
        v = (arcpy.sa.Abs(arcpy.Raster(os.path.join(arcpy.env.scratchWorkspace, "qxmean"))) + arcpy.sa.Abs(arcpy.Raster(os.path.join(arcpy.env.scratchWorkspace, "qymean")))) / area
        v.save(os.path.join(arcpy.env.scratchWorkspace, "vch_"+elev_raster[5:]))
        Vch_rasters.append(os.path.join(arcpy.env.scratchWorkspace, "vch_"+elev_raster[5:]))
        # converting the qx in vx in the floodplain
        area = arcpy.sa.Con(arcpy.sa.IsNull(width), (result - dem) * result.meanCellHeight)
        area2 = arcpy.sa.SetNull(area, area, "VALUE <= 0")
        v = arcpy.Raster(os.path.join(arcpy.env.scratchWorkspace, "qxmean")) / area2
        v.save(os.path.join(arcpy.env.scratchWorkspace, "vx_" + elev_raster[5:]))
        Vx_rasters.append(os.path.join(arcpy.env.scratchWorkspace, "vx_" + elev_raster[5:]))
        # converting the qy in vy in the floodplain
        area = arcpy.sa.Con(arcpy.sa.IsNull(width), (result - dem) * result.meanCellWidth)
        area2 = arcpy.sa.SetNull(area, area, "VALUE <= 0")
        v = arcpy.Raster(os.path.join(arcpy.env.scratchWorkspace, "qymean")) / area2
        v.save(os.path.join(arcpy.env.scratchWorkspace, "vy_" + elev_raster[5:]))
        Vy_rasters.append(os.path.join(arcpy.env.scratchWorkspace, "vy_" + elev_raster[5:]))



    ### Merging the qx and qy results by taking the value where the elevation is the maximum
    ### based on the usage of HighestPosition (with the elevation), then Pick
    # create a raster indicating which zone has the maximum elevation
    max_id = arcpy.sa.HighestPosition(tmp_elev_rasters)
    # Pick merge the vx, vy and vch rasters
    with arcpy.EnvManager(extent=max_id):
        vx_raster = arcpy.sa.Pick(max_id, Vx_rasters)
        vy_raster = arcpy.sa.Pick(max_id, Vy_rasters)
        vch_raster = arcpy.sa.Pick(max_id, Vch_rasters)
        vx_raster.save(os.path.join(res_folder, "vx"))
        vy_raster.save(os.path.join(res_folder, "vy"))
        vch_raster.save(os.path.join(res_folder, "v_channel"))


    # cleaning temp results
    arcpy.Delete_management("qymean")
    arcpy.Delete_management("qxmean")
    for raster in tmp_elev_rasters:
        arcpy.Delete_management(raster)
    for raster in Vx_rasters:
        arcpy.Delete_management(raster)
    for raster in Vy_rasters:
        arcpy.Delete_management(raster)
    for raster in Vch_rasters:
        arcpy.Delete_management(raster)


if __name__ == "__main__":
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True
    arcpy.env.scratchWorkspace = r"D:\InfoCrue\tmp"

    folder = r"D:\InfoCrue\DuNord\protprocv\vq350_revised"
    width = arcpy.Raster(r"Z:\Projects\MSP\DuNord\Lisflood_Atlas2020_Fall2020\inputs\width_d4")
    bed = arcpy.Raster(r"Z:\Projects\MSP\DuNord\Lisflood_Atlas2020_Fall2020\inputs\bed_b")
    dem = arcpy.Raster(r"Z:\Projects\MSP\DuNord\Lisflood_Atlas2020_Fall2020\inputs\lid10mavg_c")

    conversion(folder)
    postproc_v(width, bed, dem, folder)


