# -*- coding: utf-8 -*-

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Nov 2020 - Création

import arcpy
import os
import sys
from RasterIO import *

def execute_Resample(smoothed_dir, dem3m_dir, flow_dir, frompoints_dir, prefixe, river_tools_folder, output_folder, messages):

    sys.path.append(river_tools_folder)
    from Breach import execute_Breach



    arcpy.env.workspace = smoothed_dir
    rasterlist = arcpy.ListRasters()

    flowdir_output = arcpy.CreateScratchName("rres", data_type="RasterDataset", workspace=arcpy.env.scratchWorkspace)
    temp_resample = arcpy.CreateScratchName("rres", data_type="RasterDataset", workspace=arcpy.env.scratchWorkspace)
    temp_tobreach = arcpy.CreateScratchName("rres", data_type="RasterDataset", workspace=arcpy.env.scratchWorkspace)

    arcpy.env.extent = flow_dir

    for raster in rasterlist:
        print (raster)

        buffered = arcpy.sa.Float(arcpy.sa.EucAllocation(arcpy.sa.Int(arcpy.Raster(raster) * 1000))) / 1000
        with arcpy.EnvManager(snapRaster=flow_dir):
            arcpy.Resample_management(buffered, temp_resample, str(flow_dir.meanCellWidth)+" "+str(flow_dir.meanCellHeight), "BILINEAR")
        dem3m = os.path.join(dem3m_dir, raster)
        tobreach = arcpy.sa.ExtractByMask(temp_resample, dem3m)
        tobreach.save(temp_tobreach)

        newextent = str(tobreach.extent.XMin) + " " + str(tobreach.extent.YMin) + " " + str(tobreach.extent.XMax) + " " + str(tobreach.extent.YMax)
        arcpy.Clip_management(flow_dir, newextent, flowdir_output, maintain_clipping_extent="MAINTAIN_EXTENT")

        str_frompoints = os.path.join(frompoints_dir, prefixe + raster + ".shp")
        result = os.path.join(output_folder, raster)

        with arcpy.EnvManager(extent=flow_dir):
            execute_Breach(arcpy.Raster(temp_tobreach), arcpy.Raster(flowdir_output), str_frompoints, result, messages)

    arcpy.Delete_management(flowdir_output)
    arcpy.Delete_management(temp_resample)
    arcpy.Delete_management(temp_tobreach)

class Messages():
    def addErrorMessage(self, text):
        print(text)

    def addWarningMessage(self, text):
        print(text)

    def addMessage(self, text):
        print(text)

if __name__ == "__main__":
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True
    arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    messages = Messages()

    smoothed_dir = r"D:\InfoCrue\Noire\bathy\Smoothed"
    dem3m_dir = r"D:\InfoCrue\Noire\bathy\dem3m"
    flow_dir = arcpy.Raster(r"F:\MSP2\LargeScaleFloodMapping_may2020\Example_RiviereNoire\DEMs\lidar10m_fd")
    frompoints_dir = r"D:\InfoCrue\Noire\bathy\frompoints"
    prefixe = "fp_"
    river_tools_folder = r"F:\PyCharm\GISTools\RiversTools"
    output_folder = r"D:\InfoCrue\Noire\bathy\ResultWS_2"

    execute_Resample(smoothed_dir, dem3m_dir, flow_dir, frompoints_dir, prefixe, river_tools_folder, output_folder, messages)


