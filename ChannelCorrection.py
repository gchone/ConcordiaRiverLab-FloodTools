# -*- coding: utf-8 -*-

##################################################################
# Auteur: François Larouche-Tremblay, Ing, M Sc
# Description: Algorithme développé par FLT qui inverse le profil
# d'élévation de la surface de l'eau sur l'axe amont-aval et lui
# fait subir une réflexion sur le plan XY, lui ajoute des murs et
# applique l'algorithme de remplissage des cuvettes d'ESRI.
# Le résultat est ensuite retransformé dans le référentiel initial.
# Cela a pour effet de supprimer les remontées sur le lit d'une
# manière cohérente avec l'écoulement D8.
##################################################################

# Modifié par G. Choné

import arcpy
from arcpy import env, CreateScratchName
from arcpy.sa import *
from arcpy.conversion import PolygonToRaster, PolylineToRaster
from arcpy.management import CopyFeatures, AddField, CalculateField, Delete


def execute_ChannelCorrection(demras, boundary, riverbed, rivernet, DEMs_limits, breachedmnt, messages):

    arcpy.env.outputCoordinateSystem = demras.spatialReference
    env.snapRaster = demras



    ends = CreateScratchName("loob", data_type="FeatureClass", workspace="in_memory")
    CopyFeatures(boundary, ends)

    AddField(ends, "dummy", "LONG", field_alias="dummy", field_is_nullable="NULLABLE")
    CalculateField(ends, "dummy", "1", "PYTHON")

    endsras = CreateScratchName("loras", data_type="RasterDataset", workspace=env.scratchWorkspace)
    PolylineToRaster(ends, "dummy", endsras, "MAXIMUM_LENGTH", cellsize=demras)
    statpts = FocalStatistics(endsras, NbrRectangle(3, 3, "CELL"), "MAXIMUM", "DATA")

    env.extent = demras

    rasterbed = CreateScratchName("loras", data_type="RasterDataset", workspace=env.scratchWorkspace)
    PolygonToRaster(riverbed, arcpy.Describe(riverbed).OIDFieldName, rasterbed, "CELL_CENTER", cellsize=demras)
    rasterline = CreateScratchName("loras", data_type="RasterDataset", workspace=env.scratchWorkspace)
    PolylineToRaster(rivernet, arcpy.Describe(rivernet).OIDFieldName, rasterline, cellsize=demras)

    streambed = Con(IsNull(rasterline), Con(IsNull(rasterbed) == 0, 1), 1)

    bedwalls = FocalStatistics(streambed, NbrRectangle(3, 3, "CELL"), "MAXIMUM", "DATA")

    env.extent = bedwalls


    limits = CreateScratchName("limits", data_type="FeatureClass", workspace="in_memory")
    arcpy.PolygonToLine_management(DEMs_limits,
                                   limits)
    rasterlimit = CreateScratchName("loras", data_type="RasterDataset", workspace=env.scratchWorkspace)
    PolylineToRaster(limits, arcpy.Describe(limits).OIDFieldName, rasterlimit, "MAXIMUM_LENGTH", cellsize=demras)

    chanelev = Con(streambed, demras)
    chanmax = chanelev.maximum
    chanwalls = chanelev.minimum - 100

    switchelev_file = CreateScratchName("switch", data_type="RasterDataset", workspace=env.scratchWorkspace)
    switchelev = SetNull(IsNull(rasterlimit) == 0, -1 * (Con(IsNull(streambed), Con(bedwalls, Con(IsNull(statpts), chanwalls)), chanelev) - chanmax))
    switchelev.save(switchelev_file)

    Delete(rasterbed)
    Delete(bedwalls)
    Delete(endsras)
    Delete(rasterline)
    Delete(statpts)
    Delete(chanelev)

    env.extent = demras
    breachedtemp = Con(IsNull(rasterlimit) == 0, demras, Con(IsNull(streambed), demras, (-1*Fill(switchelev_file)) + chanmax))

    breachedtemp.save(breachedmnt)

    Delete(switchelev_file)
    Delete(switchelev)
    Delete(streambed)
    Delete(rasterlimit)
    # Delete(switchfilled)
    return

