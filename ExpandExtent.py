# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - November 2020 - Création



import arcpy
from RasterIO import *



def execute_ExpandExtent(r_raster_in, raster_out,  messages):

    newXMin = r_raster_in.extent.XMin - r_raster_in.meanCellWidth
    newXMax = r_raster_in.extent.XMax + r_raster_in.meanCellWidth
    newYMin = r_raster_in.extent.YMin - r_raster_in.meanCellHeight
    newYMax = r_raster_in.extent.YMax + r_raster_in.meanCellHeight

    #newextent = str(newXMin) + " " + str(newYMin) + " " + str(newXMax) + " " + str(newYMax)

    #arcpy.Clip_management(r_raster_in, newextent, raster_out, maintain_clipping_extent="NO_MAINTAIN_EXTENT")
    with arcpy.EnvManager(extent=arcpy.Extent(newXMin, newYMin, newXMax, newYMax)):
        raster2 = r_raster_in + 0
        raster2.save(raster_out)



    return



