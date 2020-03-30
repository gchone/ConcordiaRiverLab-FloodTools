# coding: latin-1

#####################################################
# Gu�nol� Chon�
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Mars 2017 - Cr�ation
# v1.1 - Juillet 2018 - S�paration de l'interface et du m�tier, s�paration de la cr�ation des points et de l'orientation
#  des sections transversales

import arcpy
from RasterIO import *


class pointflowpath:
   pass


def execute_CS(r_flowdir, str_frompoints, distance, str_cs, messages, language = "FR"):

    # Chargement des fichiers
    flowdir = RasterIO(r_flowdir)

    # Fichier temporaire cr�� dans le "Scratch folder"
    randomname = binascii.hexlify(os.urandom(6))
    temp_cs = arcpy.env.scratchWorkspace + "\\" + randomname
    Result = RasterIO(r_flowdir, temp_cs, float, -255)

    # D�compte du nombre de points de d�part pour configurer de la barre de progression
    frompointcursor = arcpy.da.SearchCursor(str_frompoints, "OID@")
    count = 0
    for frompoint in frompointcursor:
        count += 1
    progtext = "Calcul de l'emplacement des sections transversales"
    if language == "EN":
        progtext = "Placing cross-sections"
    arcpy.SetProgressor("step", progtext, 0, count, 1)
    progres = 0

    # Traitement effectu� pour chaque point de d�part
    frompointcursor = arcpy.da.SearchCursor(str_frompoints, "SHAPE@")
    for frompoint in frompointcursor:
        # Mise � jour de la barre de progression
        arcpy.SetProgressorPosition(progres)
        progres += 1

        # On prend l'objet g�om�trique (le point) associ� � la ligne dans la table
        frompointshape = frompoint[0].firstPoint

        # Conversion des coordonn�es
        currentcol = flowdir.XtoCol(frompointshape.X)
        currentrow = flowdir.YtoRow(frompointshape.Y)

        # Tests de s�curit� pour s'assurer que le point de d�part est � l'int�rieurs des rasters
        intheraster = True
        if currentcol<0 or currentcol>=flowdir.raster.width or currentrow<0 or currentrow>= flowdir.raster.height:
            intheraster = False
        elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                      flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow, currentcol) <> 8 and
                      flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and
                      flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
            intheraster = False



        totaldistance = 0
        currentdistance = 0
        lastpointdistance = 0

        # Traitement effectu� sur chaque cellule le long de l'�coulement
        while (intheraster):

            totaldistance = totaldistance + currentdistance

            # Entre deux sections transversales, les points sont mis � -999 (cela permet la d�tection des confluences)
            if totaldistance <= lastpointdistance + distance:
                Result.setValue(currentrow, currentcol, -999)
            else:
                Result.setValue(currentrow, currentcol, 1)
                lastpointdistance = totaldistance

            # On cherche le prochain point � partir du flow direction
            direction = flowdir.getValue(currentrow, currentcol)
            if (direction == 1):
                currentcol = currentcol + 1
                currentdistance = flowdir.raster.meanCellWidth
            if (direction == 2):
                currentcol = currentcol + 1
                currentrow = currentrow + 1
                currentdistance = math.sqrt(
                    flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)
            if (direction == 4):
                currentrow = currentrow + 1
                currentdistance = flowdir.raster.meanCellHeight
            if (direction == 8):
                currentcol = currentcol - 1
                currentrow = currentrow + 1
                currentdistance = math.sqrt(
                    flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)
            if (direction == 16):
                currentcol = currentcol - 1
                currentdistance = flowdir.raster.meanCellWidth
            if (direction == 32):
                currentcol = currentcol - 1
                currentrow = currentrow - 1
                currentdistance = math.sqrt(
                    flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)
            if (direction == 64):
                currentrow = currentrow - 1
                currentdistance = flowdir.raster.meanCellHeight
            if (direction == 128):
                currentcol = currentcol + 1
                currentrow = currentrow - 1
                currentdistance = math.sqrt(
                    flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)

            # Tests de s�curit� pour s'assurer que l'on ne sorte pas des rasters
            if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
                intheraster = False
            elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                          flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow, currentcol) <> 8 and
                          flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and
                          flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
                intheraster = False

            if intheraster:
                if (Result.getValue(currentrow, currentcol) <> -255):
                    # Atteinte d'un confluent
                    intheraster = False




    # On supprime les -999 du r�sultat final
    Result.save()
    raster_res = arcpy.sa.SetNull(temp_cs, temp_cs, "VALUE = -999")
    # randomname = binascii.hexlify(os.urandom(6))
    # temp_cs2 = arcpy.env.scratchWorkspace + "\\" + randomname
    # raster_res.save(temp_cs2)

    arcpy.RasterToPoint_conversion(raster_res, str_cs)


    arcpy.Delete_management(temp_cs)
    #arcpy.Delete_management(temp_cs2)
    return