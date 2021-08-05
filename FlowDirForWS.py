# -*- coding: utf-8 -*-

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

import arcpy
import os
import ArcpyGarbageCollector as gc

def execute_FlowDirForWS(routes_main, DEM3m_forws, DEMs_footprints, output_workspace, messages):

    arcpy.MakeFeatureLayer_management(DEMs_footprints, "footprints_lyr")

    try:
        footprints_OID = arcpy.Describe(DEMs_footprints).OIDFieldName
        with arcpy.da.SearchCursor(DEMs_footprints, [footprints_OID]) as cursor:
            for row in cursor:

                # Select the footprint and clip
                query = '"{}" = {}'.format(footprints_OID, str(row[0]))
                arcpy.SelectLayerByAttribute_management("footprints_lyr", "NEW_SELECTION", query)
                dem = arcpy.sa.ExtractByMask(DEM3m_forws, "footprints_lyr")

                # Create pixel-exact footprint
                bin_raster = arcpy.sa.Con(arcpy.sa.IsNull(dem) == 0, 10000)
                domain = gc.CreateScratchName("domain", data_type="FeatureClass", workspace="in_memory")
                arcpy.RasterToPolygon_conversion(bin_raster, domain, simplify="NO_SIMPLIFY")

                # Create wall around the raster
                domain_fullbuf = gc.CreateScratchName("domainb", data_type="FeatureClass", workspace="in_memory")
                arcpy.Buffer_analysis(domain, domain_fullbuf, 3)
                walls = gc.CreateScratchName("walls", data_type="RasterDataset", workspace=arcpy.env.scratchWorkspace)
                with arcpy.EnvManager(snapRaster=dem):
                    arcpy.PolygonToRaster_conversion(domain_fullbuf, "GRIDCODE", walls, cellsize=dem)

                # Find in-out points
                domain_halfbuf = gc.CreateScratchName("domainb2", data_type="FeatureClass", workspace="in_memory")
                arcpy.Buffer_analysis(domain, domain_halfbuf, 1.5)
                inoutpts = gc.CreateScratchName("inoutpts", data_type="FeatureClass", workspace="in_memory")
                arcpy.Intersect_analysis([routes_main, domain_halfbuf], inoutpts, output_type="POINT")
                inoutptss = gc.CreateScratchName("inoutptss", data_type="FeatureClass", workspace="in_memory")
                arcpy.MultipartToSinglepart_management(inoutpts, inoutptss)

                # Keep only out points
                #  Linear reference the points
                inoutpts_loc = gc.CreateScratchName("inoutptss", data_type="ArcInfoTable", workspace="in_memory")
                arcpy.LocateFeaturesAlongRoutes_lr(inoutptss, routes_main, "RID", 0.1, out_table=inoutpts_loc, out_event_properties="RID POINT MEAS")
                #arcpy.AddField_management(inoutpts_loc, "ptsid", "SHORT")
                #arcpy.CalculateField_management(inoutpts_loc, "ptsid", "!" + arcpy.Describe(inoutpts_loc).OIDFieldName + "!", "PYTHON")
                #  Add a small distance (0.1m) to the linear referencing
                arcpy.CalculateField_management(inoutpts_loc, "MEAS",
                                                "!MEAS!+0.1", "PYTHON")
                #  Turn back the result into points
                arcpy.MakeRouteEventLayer_lr(routes_main, "RID", inoutpts_loc,
                                             "RID POINT MEAS", "inout_pts_lyr")
                #  Select only the points in the polygons there were created from
                arcpy.SelectLayerByLocation_management("inout_pts_lyr", "WITHIN", domain_halfbuf)
                out_pts = gc.CreateScratchName("out_pts", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
                arcpy.CopyFeatures_management("inout_pts_lyr", out_pts)

                # Convert the out point into a raster
                out_rpts = gc.CreateScratchName("out_rpts", data_type="RasterDataset", workspace=arcpy.env.scratchWorkspace)
                with arcpy.EnvManager(snapRaster=dem):
                    with arcpy.EnvManager(extent=walls):
                        arcpy.PointToRaster_conversion(out_pts, arcpy.Describe(out_pts).OIDFieldName, out_rpts, cellsize=dem)

                # Create the walled DEM
                with arcpy.EnvManager(extent=walls):
                    walled = arcpy.sa.Con(arcpy.sa.IsNull(out_rpts),
                        arcpy.sa.Con(arcpy.sa.IsNull(dem), walls, dem))

                # Fill and Flow Dir
                fill = arcpy.sa.Fill(walled)
                flowdir = arcpy.sa.FlowDirection(fill)

                # Clip
                clip_flowdir = arcpy.sa.ExtractByMask(flowdir, dem)
                clip_flowdir.save(os.path.join(output_workspace, "dem"+str(row[0])))

                messages.addMessage("Done DEM with footprint id "+str(row[0]))


    finally:
        gc.CleanAllTempFiles()
