# coding: latin-1



##################################################################
# Auteur: Fran�ois Larouche-Tremblay, Ing, M Sc
# Description: Algorithme it�ratif d�velopp� par FLT qui permet
# de d�tecter la surface de l'eau (cases inond�es) � partir d'un raster du chenal
# ou d'un raster repr�sentant un "HAND z�ro". La fonction permet d'exclure
# les diff�rences d'�l�vation trop importantes (eltol), de filtrer le r�sultat final (postpro),
# d'imposer des zones d'exclusion (offlim) ainsi que d'imposer des br�ches (brch).
##################################################################

# Versions:
# v1.0 - Sept 2019 - Fran�ois Larouche-Tremblay - Creation
# v1.1 - May 2020 - Gu�nol� Chon� - Brought into the FloodTools package. Added global tol

import arcpy

def execute_ChanelDetection(r_streams, r_dem, niter, offlim, brch, postpro, checkelev, localtol, globaltol, watsurf, messages):
    arcpy.env.snapRaster = r_streams
    arcpy.env.extent = r_streams
    niter = max(niter, 1)
    maskras = None

    if isinstance(offlim, arcpy.Raster):
        maskras = arcpy.sa.Con(arcpy.sa.IsNull(offlim), 0)

    newstreams = arcpy.sa.Con(arcpy.sa.IsNull(r_streams), r_streams, 0) # replace channel values by 0

    if brch and brch != "#":
        brchras = arcpy.CreateScratchName("det", data_type="RasterDataset", workspace="in_memory")
        arcpy.PolylineToRaster(brch, "OBJECTID", brchras, "MAXIMUM_LENGTH", cellsize=r_dem)
        newstreams = arcpy.sa.Con(arcpy.sa.IsNull(brchras), newstreams, 0)

    growthcheck = False

    newdem = r_dem + newstreams

    for ii in range(0, niter, 1):
        localmax = arcpy.sa.FocalStatistics(newdem, arcpy.sa.NbrRectangle(3, 3, "CELL"), "MAXIMUM", "DATA")

        newstreams = arcpy.sa.Con((r_dem - localmax) <= globaltol, 0)
        if maskras is not None:  # On ajoute des z�ros partout et les NoData du masque effacent les donn�es
            newstreams = newstreams + maskras

        # on remplace les valeurs du dem par le localmax si celui-ci est plus petit
        newdem = arcpy.sa.Con((r_dem - localmax) < 0, r_dem, localmax)

        del localmax
        if growthcheck:
            checkras = arcpy.sa.Con(arcpy.sa.IsNull(newstreams), 0, 1) - oldgrowth

            if checkras.maximum == 0:
                niter = ii + 1  # Garde en m�moire le nombre r�el d'it�rations pour le postprocessing
                del checkras, oldgrowth
                break
            growthcheck = False
            del checkras, oldgrowth

        if ((ii+1) % 10) == 0:  # Test si le raster des sources a �volu� � chaque 10 nouvelles it�rations
            oldgrowth = arcpy.sa.Con(arcpy.sa.IsNull(newstreams), 0, 1)
            growthcheck = True



    if postpro:
        streamelev = r_dem + newstreams
        newstreams = newstreams + 1  # Convertit les z�ros en 1 pour le compte du nombre de voisins
        niter = niter//10 + 1  # Hardcoded: environ 10% d'it�rations pour le postprocessing
        for ii in range(0, niter, 1):
            nbneighbors = arcpy.sa.FocalStatistics(newstreams, arcpy.sa.NbrRectangle(3, 3, "CELL"), "SUM", "DATA")
            if checkelev:
                nottoohigh = r_dem - arcpy.sa.FocalStatistics(streamelev, arcpy.sa.NbrRectangle(5, 5, "CELL"), "MEAN", "DATA")
                newstreams = arcpy.sa.Con((nbneighbors >= 6) & (nottoohigh <= localtol), 1, newstreams)
                del nbneighbors, nottoohigh
            else:
                newstreams = arcpy.sa.Con(nbneighbors >= 6, 1, newstreams)
                del nbneighbors

            if maskras is not None:  # On ajoute des z�ros partout et les NoData du masque effacent les donn�es
                newstreams = newstreams + maskras
        del streamelev
    del maskras

    sources = arcpy.sa.Con(arcpy.sa.IsNull(newstreams), r_streams, r_dem)
    sources.save(watsurf)

    return