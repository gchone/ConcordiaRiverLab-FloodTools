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

# Versions:
# v1.0 - Sept 2019 - François Larouche-Tremblay - Creation
# v1.1 - May 2020 - Guénolé Choné - Pour package FloodTools. Ajout de la ligne de cours d'eau pour assurer un pixel de large
#    Utilisation d'un raster en m. Extent = dem par défaut. Coordinate system = dem

import arcpy
from arcpy import env, CreateScratchName
from arcpy.sa import *
from arcpy.conversion import PolygonToRaster, PolylineToRaster
from arcpy.management import CopyFeatures, AddField, CalculateField, Delete


def execute_ChannelCorrection(demras, boundary, riverbed, rivernet, breachedmnt, messages):

    arcpy.env.outputCoordinateSystem = demras.spatialReference
    env.snapRaster = demras
    env.extent = demras

    rasterbed = CreateScratchName("loras", data_type="RasterDataset", workspace="in_memory")
    PolygonToRaster(riverbed, arcpy.Describe(riverbed).OIDFieldName, rasterbed, "CELL_CENTER", cellsize=demras)
    rasterline = CreateScratchName("loras", data_type="RasterDataset", workspace="in_memory")
    PolylineToRaster(rivernet, arcpy.Describe(rivernet).OIDFieldName, rasterline, cellsize=demras)

    streambed = Con(IsNull(rasterline), Con(IsNull(rasterbed) == 0, 1), 1)
    ends = CreateScratchName("loob", data_type="FeatureClass", workspace="in_memory")
    CopyFeatures(boundary, ends)

    AddField(ends, "dummy", "LONG", field_alias="dummy", field_is_nullable="NULLABLE")
    CalculateField(ends, "dummy", "1", "PYTHON")

    endsras = CreateScratchName("loras", data_type="RasterDataset", workspace="in_memory")
    PolylineToRaster(ends, "dummy", endsras, "MAXIMUM_LENGTH", cellsize=demras)
    statpts = FocalStatistics(endsras, NbrRectangle(3, 3, "CELL"), "MAXIMUM", "DATA")
    bedwalls = FocalStatistics(streambed, NbrRectangle(3, 3, "CELL"), "MAXIMUM", "DATA")

    env.extent = bedwalls

    chanelev = Con(streambed, demras)
    chanmax = chanelev.maximum
    chanwalls = chanelev.minimum - 100
    switchtemp = CreateScratchName("loras", data_type="RasterDataset", workspace=env.scratchWorkspace)
    switchelev = -1 * (Con(IsNull(streambed), Con(bedwalls, Con(IsNull(statpts), chanwalls)), chanelev) - chanmax)
    switchelev.save(switchtemp)
    Delete(statpts)
    Delete(chanelev)

    switchfilled = Fill(switchtemp)
    Delete(switchtemp)

    env.extent = demras
    breachedtemp = Con(IsNull(streambed), demras, (-1*switchfilled) + chanmax)
    breachedtemp.save(breachedmnt)

    Delete(bedwalls)
    Delete(switchfilled)
    return

