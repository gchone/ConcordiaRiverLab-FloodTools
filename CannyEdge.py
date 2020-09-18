# -*- coding: utf-8 -*-

import numpy
import cv2
import arcpy
import binascii
import os

def execute_CannyEdge(str_raster, sigma, threshold1, threshold2, result, messages):


    randomname = binascii.hexlify(os.urandom(6)).decode()
    filetemp = arcpy.env.scratchWorkspace + "\\" + str(randomname) + ".tif"


    arcpy.CopyRaster_management(str_raster, filetemp, pixel_type="8_BIT_UNSIGNED")

    img = cv2.imread(filetemp, cv2.IMREAD_GRAYSCALE)

    originalraster = arcpy.Raster(str_raster)

    # Blur: to reproduce the OPALS Canny edge behaviour, the kernel radius is set to 3 times the standard deviation
    # the kernel size should be however minimum 3, and size%2 ==1 (i.e. is can be 3, 5 ,7 ,9, etc.)
    kernel_size = max(1, int(round(sigma*3)))*2+1
    blur = cv2.GaussianBlur(img, (kernel_size, kernel_size), sigma)
    edges = cv2.Canny(blur, threshold1, threshold2)
    resraster = arcpy.NumPyArrayToRaster(edges, arcpy.Point(originalraster.extent.XMin, originalraster.extent.YMin),
                                         originalraster.meanCellWidth, originalraster.meanCellHeight, originalraster.noDataValue)
    resraster.save(result)
    arcpy.Delete_management(filetemp)



