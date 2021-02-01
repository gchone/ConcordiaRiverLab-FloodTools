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



def execute_DEMsDownstreamCorrection(ends_polygons_dir, dem_bridges_dir, output_folder, messages):


    arcpy.env.workspace = ends_polygons_dir
    polylist = arcpy.ListFeatureClasses()

    for poly in polylist:

        rastername = os.path.splitext(poly)[0]
        print (rastername)
        dem = os.path.join(dem_bridges_dir, rastername)
        arcpy.env.extent = dem

        # Converting the polygons in rasters
        lines = arcpy.CreateScratchName("lines", data_type="FeatureClass", workspace="in_memory")
        arcpy.PolygonToLine_management(poly, lines, "IGNORE_NEIGHBORS")

        r_lines = arcpy.CreateScratchName("rlines", data_type="RasterDataset",
                                                workspace=arcpy.env.scratchWorkspace)
        arcpy.PolylineToRaster_conversion(lines, "ORIG_FID", r_lines, cellsize=dem)

        r_poly = arcpy.CreateScratchName("rpoly", data_type="RasterDataset",
                                                workspace=arcpy.env.scratchWorkspace)
        arcpy.PolygonToRaster_conversion(poly, arcpy.Describe(poly).OIDFieldName, r_poly,
                                         cellsize=dem)


        rasterized = arcpy.sa.Con(arcpy.sa.IsNull(r_lines),  arcpy.sa.SetNull(arcpy.sa.IsNull(r_poly), 1), 1)
        rasterized.save(os.path.join(ends_polygons_dir, rastername))

        # Correcting the DEMs
        dem = os.path.join(dem_bridges_dir, rastername)
        correcteddem = arcpy.sa.Con(arcpy.sa.IsNull(rasterized), dem)
        correcteddem.save(os.path.join(output_folder, rastername))

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

    ends_polygons_dir = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\DEMsOutputCorrections"
    dem_bridges_dir = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\DEM3m"
    output_folder = r"D:\InfoCrue\Etchemin\DEMbydays\PythonProcessing\CorrectedDEMs"

    execute_DEMsDownstreamCorrection(ends_polygons_dir, dem_bridges_dir, output_folder, messages)


