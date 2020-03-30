# coding: latin-1

#####################################################
# Gu�nol� Chon�
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Mars 2017 - Cr�ation
# v1.1 - Juin 2018 - S�paration de l'interface et du m�tier
# v1.2 - Novembre 2018 - D�bogage aux confluences

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

    # Liste des nouveaux points de d�part
    listfirstpoints = []
    # D�compte du nombre de points de d�part pour configurer de la barre de progression
    frompointcursor = arcpy.da.SearchCursor(str_frompoint, "OID@")
    count = 0
    for frompoint in frompointcursor:
        count += 1
    progtext = "Calcul des pentes"
    if language == "EN":
        progtext = "Processing"
    arcpy.SetProgressor("step", progtext, 0, count, 1)
    progres = 0
    # Traitement effectu� pour chaque point de d�part
    frompointcursor = arcpy.da.SearchCursor(str_frompoint, "SHAPE@")
    for frompoint in frompointcursor:

        # Mise � jour de la barre de progression
        arcpy.SetProgressorPosition(progres)
        progres += 1

        # On prend l'objet g�om�trique (le point) associ� � la ligne dans la table
        frompointshape = frompoint[0].firstPoint

        # Conversion des coordonn�es
        currentcol = FlowDir.XtoCol(frompointshape.X)
        currentrow = FlowDir.YtoRow(frompointshape.Y)

        intheraster = True
        # Tests de s�curit� pour s'assurer que le point de d�part est � l'int�rieurs des rasters
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

        # Traitement effectu� sur chaque cellule le long de l'�coulement
        while (intheraster):

            # On met � jour la liste des points le long de l'�coulement
            currentpoint = pointflowpath()
            currentpoint.row = currentrow
            currentpoint.col = currentcol
            currentpoint.addeddistance = currentdistance
            totaldistance = totaldistance + currentdistance
            currentpoint.distance = totaldistance
            listpointsflowpath.append(currentpoint)

            # les points sont mis � -999 (cela permet la d�tection des confluences)
            if confluencedist == 0:
                Result.setValue(currentrow, currentcol, -999)

            # On cherche le prochain point � partir du flow direction
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

            # Tests de s�curit� pour s'assurer que l'on ne sorte pas des rasters
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

                    # On continue encore sur la distance de calcul de la pente apr�s le confluent
                    if (totaldistance + currentdistance - confluencedist) > distancesmoothingpath:
                        intheraster = False





        currentpointnumber = 0
        # Pour chaque point le long de l'�coulement
        while (currentpointnumber < len(listpointsflowpath)):


            currentpoint = listpointsflowpath[currentpointnumber]


            listpointforregression = []
            listpointforregression.append(currentpoint)
            distancefromcurrentpoint = 0
            nbcellsfromcurrentpoint = 0
            try:
                # on s'�loigne du point courant, en allant vers l'amont, jusqu'� d�passer la distance de calcul de la pente
                while (distancefromcurrentpoint <= distancesmoothingpath / 2):
                    nbcellsfromcurrentpoint = nbcellsfromcurrentpoint - 1
                    if (currentpointnumber + nbcellsfromcurrentpoint >= 0):
                        # on mets � jour la distance jusqu'au point courant
                        distancefromcurrentpoint = distancefromcurrentpoint + listpointsflowpath[
                            currentpointnumber + nbcellsfromcurrentpoint].addeddistance
                        # on ajoute le point aux points � utiliser pour la r�gression (calcul de la pente au point courant)
                        listpointforregression.append(
                            listpointsflowpath[currentpointnumber + nbcellsfromcurrentpoint])
                    else:
                        # la distance � l'extr�mit� amont est plus petie que la distance de calcul de pente
                        raise IndexError
                distancefromcurrentpoint = 0
                nbcellsfromcurrentpoint = 0
                # m�me chose en s'�liognant du point courant vers l'aval
                while (distancefromcurrentpoint < distancesmoothingpath / 2):
                    nbcellsfromcurrentpoint = nbcellsfromcurrentpoint + 1
                    if (currentpointnumber + nbcellsfromcurrentpoint < len(listpointsflowpath)):
                        distancefromcurrentpoint = distancefromcurrentpoint + listpointsflowpath[
                            currentpointnumber + nbcellsfromcurrentpoint].addeddistance
                        listpointforregression.append(listpointsflowpath[currentpointnumber + nbcellsfromcurrentpoint])
                    else:
                        # la distance � l'extr�mit� aval est plus petite que la distance de calcul de pente
                        raise IndexError

                # Calcul de la r�gression lin�aire
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
                    # S'il s'agit du premier point (pour ce point de d�part) pour lequel une valeur de pente est calcul�e, on enregistre ce point dans la liste des points de d�part des pentes
                    newpoint = arcpy.Point(FlowDir.raster.extent.XMin + (currentpoint.col + 0.5) * FlowDir.raster.meanCellWidth,
                                           FlowDir.raster.extent.YMax - (currentpoint.row + 0.5) * FlowDir.raster.meanCellHeight)
                    listfirstpoints.append(newpoint)
                    firstpoint = False


            except IndexError:
                # pas de calcul de la pente pour les extr�mit� amont et aval (il n'y a pas la distance suffisante pour le calcul de la pente)
                pass



            currentpointnumber = currentpointnumber + 1


    Result.save()
    # On supprime les -999 du r�sultat final
    raster_res = arcpy.sa.SetNull(save_slope, save_slope, "VALUE = -999")
    raster_res.save(save_slope)

    # on enregistre la liste des points de d�part des pente
    arcpy.CreateFeatureclass_management(os.path.dirname(save_newfp),
                                        os.path.basename(save_newfp), "POINT", spatial_reference=r_flowdir)
    pointcursor = arcpy.da.InsertCursor(save_newfp, "SHAPE@XY")
    for point in listfirstpoints:
        pointcursor.insertRow([(point.X, point.Y)])

    return