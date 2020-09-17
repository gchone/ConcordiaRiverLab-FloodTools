# -*- coding: utf-8 -*-

import numpy
import cv2
import arcpy
import binascii
import os

def execute_CannyEdge(str_raster, sigma, threshold1, threshold2, result, messages):


    randomname = binascii.hexlify(os.urandom(6))
    filetemp = arcpy.env.scratchWorkspace + "\\" + randomname + ".tif"


    arcpy.CopyRaster_management(str_raster, filetemp, pixel_type="8_BIT_UNSIGNED")

    img = cv2.imread(filetemp, cv2.IMREAD_GRAYSCALE)

    originalraster = arcpy.Raster(str_raster)

    # Blur: to reproduce the OPALS Canny edge behaviour, the kernel size is set to 3 times the standard deviation
    blur = cv2.GaussianBlur(img, (int(3*sigma), int(3*sigma)), sigma)
    edges = cv2.Canny(blur, threshold1, threshold2)
    resraster = arcpy.NumPyArrayToRaster(edges, arcpy.Point(originalraster.extent.XMin, originalraster.extent.YMin),
                                         originalraster.meanCellWidth, originalraster.meanCellHeight, originalraster.noDataValue)
    resraster.save(result)
    arcpy.Delete_management(filetemp)



