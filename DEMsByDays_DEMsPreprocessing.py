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
from ExpandExtent import *

def execute_DEMsPreprocessing(dem1m_dir, bridges_poly, river_tools_folder, output_folder, messages):

    sys.path.append(river_tools_folder)
    from BridgeCorrection import execute_BridgeCorrection

    arcpy.env.workspace = dem1m_dir
    rasterlist = arcpy.ListRasters()
    r_demcorrect = arcpy.CreateScratchName("rdem", data_type="RasterDataset",
                                           workspace=arcpy.env.scratchWorkspace)
    for raster in rasterlist:
        print raster
        raster3m = arcpy.sa.Aggregate(raster, 3, aggregation_type="MINIMUM")

        execute_BridgeCorrection(raster3m, bridges_poly, r_demcorrect, messages)
        execute_ExpandExtent(arcpy.Raster(r_demcorrect), os.path.join(output_folder, raster), messages)

        arcpy.env.snapRaster = os.path.join(output_folder, raster)

    arcpy.Delete_management(r_demcorrect)



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

    dem1m_dir = r"D:\InfoCrue\Etchemin\DEMbydays\Original1mdems"
    bridges_poly = r"Z:\Projects\MSP\Etchemin\LisfloodJuly2020\Bridges_Polygon.shp"
    river_tools_folder = r"F:\PyCharm\GISTools\RiversTools"
    output_folder = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\DEM3m"

    execute_DEMsPreprocessing(dem1m_dir, bridges_poly, river_tools_folder, output_folder, messages)


