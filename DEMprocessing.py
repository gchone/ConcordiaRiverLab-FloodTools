# -*- coding: utf-8 -*-

import os
import arcpy


def execute_BatchAggregate(dem3m_list, cell_factor, aggregation_type, extent_handling, ignore_nodata, output_dir, messages):

    arcpy.env.workspace = dem3m_dir
    rasterlist = arcpy.ListRasters()

    first_iter = True
    for raster in rasterlist:

        if first_iter:
            aggregated = arcpy.sa.Aggregate(raster, cell_factor, aggregation_type, extent_handling, ignore_nodata)
            snap = aggregated
            first_iter = False
        else:
            with arcpy.EnvManager(snapRaster=snap):
                aggregated = arcpy.sa.Aggregate(raster, cell_factor, aggregation_type, extent_handling, ignore_nodata)
        save_path = os.path.join(output_dir, raster)
        aggregated.save(save_path)

