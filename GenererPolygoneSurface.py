# -*- coding: utf-8 -*-

##################################################################
# Auteur: François Larouche-Tremblay, Ing, M Sc
# Date: 24/04/2020
# Description: Génère un polygone de surface de l'eau à partir du
# raster des sources en effectuant une suite d'extension-contraction
##################################################################

import arcpy
from arcpy import env, CreateScratchName
from arcpy.sa import *
from arcpy.conversion import RasterToPolygon
from arcpy.analysis import GraphicBuffer, Erase
from arcpy.management import Delete, EliminatePolygonPart, MultipartToSinglepart, Merge, Dissolve


def execute_GenererPolygoneSurface(watsurf, maxwidth, minwidth, islands, surface, messages):
    sws = env.scratchWorkspace
    env.extent = watsurf
    watras = Raster(watsurf)
    cellsize = int(watras.meanCellHeight)

    bedpoly = CreateScratchName("gepo", data_type="FeatureClass", workspace=sws)
    RasterToPolygon(watsurf, bedpoly, "NO_SIMPLIFY", "VALUE", "MULTIPLE_OUTER_PART")

    islandup = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
    GraphicBuffer(bedpoly, islandup, "{0} Meters".format(cellsize), "SQUARE", "MITER", 10, "0 Meters")
    Delete(bedpoly)

    smoothed = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
    GraphicBuffer(islandup, smoothed, "{0} Meters".format(-cellsize), "SQUARE", "MITER", 10, "0 Meters")

    fillbed = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
    EliminatePolygonPart(smoothed, fillbed, "PERCENT", "0 SquareMeters", 50, "CONTAINED_ONLY")

    multiland = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
    Erase(fillbed, smoothed, multiland, None)
    MultipartToSinglepart(multiland, islands)

    mindist = max(cellsize, int(minwidth / (2 * cellsize)) * cellsize)
    maxdist = max(mindist, int(maxwidth / (2 * cellsize)) * cellsize)
    gblist = list(range(mindist, maxdist + cellsize, cellsize))
    scalelist = ["" for ii in range(0, len(gblist), 1)]
    partlist = []
    scaledn = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
    GraphicBuffer(smoothed, scaledn, "{0} Meters".format(-cellsize / 2), "SQUARE", "MITER", 10, "0 Meters")

    trimmed = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
    GraphicBuffer(scaledn, trimmed, "{0} Meters".format(cellsize / 2), "SQUARE", "MITER", 10, "0 Meters")

    thins = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
    Erase(smoothed, trimmed, thins)

    inflated = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
    GraphicBuffer(thins, inflated, "{0} Meters".format(cellsize / 2), "SQUARE", "MITER", 10, "0 Meters")
    partlist.append(inflated)

    scalelist[0] = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
    if gblist[0] == cellsize:
        GraphicBuffer(trimmed, scalelist[0], "{0} Meters".format(-cellsize), "SQUARE", "MITER", 10, "0 Meters")
        partlist.append(trimmed)
        del gblist[0]
        fdist = 3*cellsize
    else:
        scalelist[0] = trimmed
        fdist = gblist[0]

    ii = 0
    for gbdist in gblist:
        scaleup = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
        GraphicBuffer(scalelist[ii], scaleup, "{0} Meters".format(fdist), "SQUARE", "MITER", 10, "0 Meters")
        fdist = (2 * gbdist) + cellsize

        smoothed = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
        GraphicBuffer(scaleup, smoothed, "{0} Meters".format(-gbdist), "SQUARE", "MITER", 10, "0 Meters")

        if ii < len(gblist)-1:
            scalelist[ii+1] = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
            GraphicBuffer(smoothed, scalelist[ii+1], "{0} Meters".format(-gbdist), "SQUARE", "MITER", 10, "0 Meters")

        partlist.append(smoothed)
        ii += 1

    merged = CreateScratchName("gepo", data_type="FeatureClass", workspace="in_memory")
    Merge(partlist, merged)
    Dissolve(merged, surface, "ORIG_FID", "", "MULTI_PART", "DISSOLVE_LINES")

    return
