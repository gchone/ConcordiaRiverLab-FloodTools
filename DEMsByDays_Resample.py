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

def execute_Resample(resamle_dir, flow_dir, frompoints_dir, prefixe, river_tools_folder, output_folder, messages):

    sys.path.append(river_tools_folder)
    from Breach import execute_Breach

    arcpy.env.workspace = resamle_dir
    rasterlist = arcpy.ListRasters()

    flowdir_output = arcpy.CreateScratchName("rfdir", data_type="RasterDataset", workspace=arcpy.env.scratchWorkspace)

    for raster in rasterlist:
        print (raster)

        arcpy.Clip_management(flow_dir, raster, flowdir_output, maintain_clipping_extent="MAINTAIN_EXTENT")

        str_frompoints = os.path.join(frompoints_dir, prefixe + raster + ".shp")
        result = os.path.join(output_folder, raster)
        execute_Breach(raster, flowdir_output, str_frompoints, result, messages)

    arcpy.Delete_management(flowdir_output)

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

    resamle_dir = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\Resampled10m"
    flow_dir = arcpy.Raster(r"D:\InfoCrue\Etchemin\DEMbydays\lidar10m_fd")
    frompoints_dir = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\FromPoints"
    prefixe = "fp_"
    river_tools_folder = r"F:\PyCharm\GISTools\RiversTools"
    output_folder = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\ResultWS"

    execute_Resample(resamle_dir, flow_dir, frompoints_dir, prefixe, river_tools_folder, output_folder, messages)


