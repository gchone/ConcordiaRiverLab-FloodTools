# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Mars 2017 - Création
# v1.1 - Juin 2018 - Séparation de l'interface et du métier
# v1.2 - Novembre 2018 - Débogage aux confluences

import arcpy
from RasterIO import *


class pointflowpath:
   pass



def execute_Slope(r_dem, r_flowdir, str_frompoint, distancesmoothingpath, save_slope, save_newfp, messages, language = "FR"):


    # Chargement des fichiers
    DEM = RasterIO(r_dem)
    FlowDir = RasterIO(r_flowdir)
    try:
        DEM.checkMatch(FlowDir)
    except Exception as e:
        messages.addErrorMessage(e.message)


    Result = RasterIO(r_flowdir, save_slope, float,-255)

    # Liste des nouveaux points de départ
    listfirstpoints = []
    # Décompte du nombre de points de départ pour configurer de la barre de progression
    frompointcursor = arcpy.da.SearchCursor(str_frompoint, "OID@")
    count = 0
    for frompoint in frompointcursor:
        count += 1
    progtext = "Calcul des pentes"
    if language == "EN":
        progtext = "Processing"
    arcpy.SetProgressor("step", progtext, 0, count, 1)
    progres = 0
    # Traitement effectué pour chaque point de départ
    frompointcursor = arcpy.da.SearchCursor(str_frompoint, "SHAPE@")
    for frompoint in frompointcursor:

        # Mise à jour de la barre de progression
        arcpy.SetProgressorPosition(progres)
        progres += 1

        # On prend l'objet géométrique (le point) associé à la ligne dans la table
        frompointshape = frompoint[0].firstPoint

        # Conversion des coordonnées
        currentcol = FlowDir.XtoCol(frompointshape.X)
        currentrow = FlowDir.YtoRow(frompointshape.Y)

        intheraster = True
        # Tests de sécurité pour s'assurer que le point de départ est à l'intérieurs des rasters
        if currentcol<0 or currentcol>=FlowDir.raster.width or currentrow<0 or currentrow>= FlowDir.raster.height:
            intheraster = False
        elif (FlowDir.getValue(currentrow, currentcol) <> 1 and FlowDir.getValue(currentrow, currentcol) <> 2 and
                            FlowDir.getValue(currentrow, currentcol) <> 4 and FlowDir.getValue(currentrow, currentcol) <> 8 and
                            FlowDir.getValue(currentrow, currentcol) <> 16 and FlowDir.getValue(currentrow, currentcol) <> 32 and FlowDir.getValue(currentrow, currentcol) <> 64 and FlowDir.getValue(currentrow, currentcol) <> 128):
            intheraster = False


        listpointsflowpath = []
        totaldistance = 0
        currentdistance = 0
        confluencedist = 0

        firstpoint = True

        # Traitement effectué sur chaque cellule le long de l'écoulement
        while (intheraster):

            # On met à jour la liste des points le long de l'écoulement
            currentpoint = pointflowpath()
            currentpoint.row = currentrow
            currentpoint.col = currentcol
            currentpoint.addeddistance = currentdistance
            totaldistance = totaldistance + currentdistance
            currentpoint.distance = totaldistance
            listpointsflowpath.append(currentpoint)

            # les points sont mis à -999 (cela permet la détection des confluences)
            if confluencedist == 0:
                Result.setValue(currentrow, currentcol, -999)

            # On cherche le prochain point à partir du flow direction
            direction = FlowDir.getValue(currentrow, currentcol)
            if (direction == 1):
                currentcol = currentcol + 1
                currentdistance = FlowDir.raster.meanCellWidth
            if (direction == 2):
                currentcol = currentcol + 1
                currentrow = currentrow + 1
                currentdistance = math.sqrt(
                    FlowDir.raster.meanCellWidth * FlowDir.raster.meanCellWidth + FlowDir.raster.meanCellHeight * FlowDir.raster.meanCellHeight)
            if (direction == 4):
                currentrow = currentrow + 1
                currentdistance = FlowDir.raster.meanCellHeight
            if (direction == 8):
                currentcol = currentcol - 1
                currentrow = currentrow + 1
                currentdistance = math.sqrt(
                    FlowDir.raster.meanCellWidth * FlowDir.raster.meanCellWidth + FlowDir.raster.meanCellHeight * FlowDir.raster.meanCellHeight)
            if (direction == 16):
                currentcol = currentcol - 1
                currentdistance = FlowDir.raster.meanCellWidth
            if (direction == 32):
                currentcol = currentcol - 1
                currentrow = currentrow - 1
                currentdistance = math.sqrt(
                    FlowDir.raster.meanCellWidth * FlowDir.raster.meanCellWidth + FlowDir.raster.meanCellHeight * FlowDir.raster.meanCellHeight)
            if (direction == 64):
                currentrow = currentrow - 1
                currentdistance = FlowDir.raster.meanCellHeight
            if (direction == 128):
                currentcol = currentcol + 1
                currentrow = currentrow - 1
                currentdistance = math.sqrt(
                    FlowDir.raster.meanCellWidth * FlowDir.raster.meanCellWidth + FlowDir.raster.meanCellHeight * FlowDir.raster.meanCellHeight)

            # Tests de sécurité pour s'assurer que l'on ne sorte pas des rasters
            if currentcol < 0 or currentcol >= FlowDir.raster.width or currentrow < 0 or currentrow >= FlowDir.raster.height:
                intheraster = False
            elif (FlowDir.getValue(currentrow, currentcol) <> 1 and FlowDir.getValue(currentrow, currentcol) <> 2 and
                            FlowDir.getValue(currentrow, currentcol) <> 4 and FlowDir.getValue(currentrow, currentcol) <> 8 and
                            FlowDir.getValue(currentrow, currentcol) <> 16 and FlowDir.getValue(currentrow, currentcol) <> 32 and FlowDir.getValue(currentrow, currentcol) <> 64 and FlowDir.getValue(currentrow, currentcol) <> 128):
                intheraster = False

            if intheraster:
                if (Result.getValue(currentrow, currentcol) <> -255):
                    # Atteinte d'un confluent
                    if confluencedist == 0:
                        confluencedist = totaldistance + currentdistance

                    # On continue encore sur la distance de calcul de la pente après le confluent
                    if (totaldistance + currentdistance - confluencedist) > distancesmoothingpath:
                        intheraster = False





        currentpointnumber = 0
        # Pour chaque point le long de l'écoulement
        while (currentpointnumber < len(listpointsflowpath)):


            currentpoint = listpointsflowpath[currentpointnumber]


            listpointforregression = []
            listpointforregression.append(currentpoint)
            distancefromcurrentpoint = 0
            nbcellsfromcurrentpoint = 0
            try:
                # on s'éloigne du point courant, en allant vers l'amont, jusqu'à dépasser la distance de calcul de la pente
                while (distancefromcurrentpoint <= distancesmoothingpath / 2):
                    nbcellsfromcurrentpoint = nbcellsfromcurrentpoint - 1
                    if (currentpointnumber + nbcellsfromcurrentpoint >= 0):
                        # on mets à jour la distance jusqu'au point courant
                        distancefromcurrentpoint = distancefromcurrentpoint + listpointsflowpath[
                            currentpointnumber + nbcellsfromcurrentpoint].addeddistance
                        # on ajoute le point aux points à utiliser pour la régression (calcul de la pente au point courant)
                        listpointforregression.append(
                            listpointsflowpath[currentpointnumber + nbcellsfromcurrentpoint])
                    else:
                        # la distance à l'extrémité amont est plus petie que la distance de calcul de pente
                        raise IndexError
                distancefromcurrentpoint = 0
                nbcellsfromcurrentpoint = 0
                # même chose en s'éliognant du point courant vers l'aval
                while (distancefromcurrentpoint < distancesmoothingpath / 2):
                    nbcellsfromcurrentpoint = nbcellsfromcurrentpoint + 1
                    if (currentpointnumber + nbcellsfromcurrentpoint < len(listpointsflowpath)):
                        distancefromcurrentpoint = distancefromcurrentpoint + listpointsflowpath[
                            currentpointnumber + nbcellsfromcurrentpoint].addeddistance
                        listpointforregression.append(listpointsflowpath[currentpointnumber + nbcellsfromcurrentpoint])
                    else:
                        # la distance à l'extrémité aval est plus petite que la distance de calcul de pente
                        raise IndexError

                # Calcul de la régression linéaire
                sumdistance = 0
                sumelevation = 0
                sumdistanceelevation = 0
                sumsquaredistance = 0
                for pointforregression in listpointforregression:
                    sumdistance = sumdistance + pointforregression.distance
                    sumelevation = sumelevation + DEM.getValue(pointforregression.row,pointforregression.col)
                    sumdistanceelevation = sumdistanceelevation + pointforregression.distance * \
                                                                  DEM.getValue(pointforregression.row,
                                                                               pointforregression.col)
                    sumsquaredistance = sumsquaredistance + pointforregression.distance * pointforregression.distance


                slope = -(len(listpointforregression) * sumdistanceelevation - sumdistance * sumelevation) / (
                    len(listpointforregression) * sumsquaredistance - sumdistance * sumdistance)

                Result.setValue(currentpoint.row, currentpoint.col, slope)

                if firstpoint:
                    # S'il s'agit du premier point (pour ce point de départ) pour lequel une valeur de pente est calculée, on enregistre ce point dans la liste des points de départ des pentes
                    newpoint = arcpy.Point(FlowDir.raster.extent.XMin + (currentpoint.col + 0.5) * FlowDir.raster.meanCellWidth,
                                           FlowDir.raster.extent.YMax - (currentpoint.row + 0.5) * FlowDir.raster.meanCellHeight)
                    listfirstpoints.append(newpoint)
                    firstpoint = False


            except IndexError:
                # pas de calcul de la pente pour les extrémité amont et aval (il n'y a pas la distance suffisante pour le calcul de la pente)
                pass



            currentpointnumber = currentpointnumber + 1


    Result.save()
    # On supprime les -999 du résultat final
    raster_res = arcpy.sa.SetNull(save_slope, save_slope, "VALUE = -999")
    raster_res.save(save_slope)

    # on enregistre la liste des points de départ des pente
    arcpy.CreateFeatureclass_management(os.path.dirname(save_newfp),
                                        os.path.basename(save_newfp), "POINT", spatial_reference=r_flowdir)
    pointcursor = arcpy.da.InsertCursor(save_newfp, "SHAPE@XY")
    for point in listfirstpoints:
        pointcursor.insertRow([(point.X, point.Y)])

    return