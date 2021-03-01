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
from ChannelCorrection import *

def execute_WaterSurfaceCorrection(correctedDEMs_dir, channel_poly_dir, prefixe, polycuts, river_network, output_folder, messages):


    arcpy.env.workspace = correctedDEMs_dir
    rasterlist = arcpy.ListRasters()


    for raster in rasterlist:
        print (raster)

        channelpoly = os.path.join(channel_poly_dir, prefixe+raster+".shp")

        execute_ChannelCorrection2(arcpy.Raster(raster), polycuts, channelpoly, river_network, os.path.join(output_folder, raster), messages)





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

    correctedDEMs_dir = r"D:\InfoCrue\Noire\bathy\ws_step2"
    channel_poly_dir = r"D:\InfoCrue\Noire\bathy\channelpoly"
    prefixe = "ch_"
    polycuts = r"D:\InfoCrue\Noire\bathy\focal_cuts"
    river_network = r"D:\InfoCrue\Noire\river_network.shp"
    output_folder = r"D:\InfoCrue\Noire\bathy\ws_step3"

    execute_WaterSurfaceCorrection(correctedDEMs_dir, channel_poly_dir, prefixe, polycuts, river_network, output_folder, messages)


