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
from WSsmoothing import *

def execute_Smooth(DEMsForWS_dir, ends_polygons_dir, frompoints_dir, prefixe, dems_dir, smoothed_output, messages):


    arcpy.env.workspace = DEMsForWS_dir
    rasterlist = arcpy.ListRasters()

    flowdir_output = arcpy.CreateScratchName("rfdir", data_type="RasterDataset", workspace=arcpy.env.scratchWorkspace)

    for raster in rasterlist:
        print raster

        # add 10000m all around the raster, and put NoData at the downstream ends
        downends = os.path.join(ends_polygons_dir, raster)
        focal = arcpy.sa.FocalStatistics(raster, arcpy.sa.NbrRectangle(3, 3, "CELL"), "MAXIMUM", "DATA")
        newdem = arcpy.sa.Con(arcpy.sa.IsNull(downends), arcpy.sa.Con(arcpy.sa.IsNull(raster), arcpy.sa.Con(arcpy.sa.IsNull(focal) == 0, 10000), raster))

        # Fill and Flow Direction
        fill = arcpy.sa.Fill(newdem)
        #fill.save(os.path.join(fill_output, raster))
        flowdir = arcpy.sa.FlowDirection(fill)

        flowdir.save(os.path.join(flowdir_output, raster))

        # Smooth
        str_frompoints = os.path.join(frompoints_dir, prefixe+raster+".shp")
        dem = arcpy.Raster(os.path.join(dems_dir, raster))
        result = os.path.join(smoothed_output, raster)
        execute_WSsmoothing(flowdir, str_frompoints, fill, dem, result)

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

    DEMsForWS_dir = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\DEMforWS"
    ends_polygons_dir = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\DEMsOutputCorrections"
    frompoints = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\FromPoints"
    prefixe = "fp_"
    dems = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\DEM3m"
    smoothed_output = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\Smoothed"



    execute_Smooth(DEMsForWS_dir, ends_polygons_dir, frompoints, prefixe, dems, smoothed_output, messages)


