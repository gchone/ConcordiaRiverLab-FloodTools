# coding: latin-1

#####################################################
# Gu�nol� Chon�
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Mars 2017 - Cr�ation
# v1.1 - Juin 2018 - S�paration de l'interface et du m�tier, ajout du traitement �tendu apr�s les confluences
# v1.2 - Novembre 2018 - D�bogage au niveau des confluences

import arcpy
from RasterIO import *


def execute_Breach(r_dem, r_flowdir, str_frompoint, SaveResult, messages, language="FR"):


    # Chargement des fichiers
    dem = RasterIO(r_dem)
    flowdir = RasterIO(r_flowdir)
    try:
        dem.checkMatch(flowdir)
    except Exception as e:
        messages.addErrorMessage(e.message)
    Result = RasterIO(r_flowdir, SaveResult, float,-255)

    # Traitement effectu� pour chaque point de d�part
    frompointcursor = arcpy.da.SearchCursor(str_frompoint, "SHAPE@")
    for frompoint in frompointcursor:

        # On prend l'objet g�om�trique (le point) associ� � la ligne dans la table
        frompointshape = frompoint[0].firstPoint

        # Conversion des coordonn�es
        currentcol = flowdir.XtoCol(frompointshape.X)
        currentrow = flowdir.YtoRow(frompointshape.Y)

        # prev_z : �l�vation au point pr�c�dent (= �l�vation du point test� pour le premier point)
        prev_z = dem.getValue(currentrow, currentcol)

        # Tests de s�curit� pour s'assurer que le point de d�part est � l'int�rieurs des rasters
        intheraster = True
        if currentcol<0 or currentcol>=flowdir.raster.width or currentrow<0 or currentrow>= flowdir.raster.height:
            intheraster = False
        elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                            flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow, currentcol) <> 8 and
                            flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
            intheraster = False

        confluence = False

        # Traitement effectu� sur chaque cellule le long de l'�coulement
        while (intheraster):


            if not confluence:
                # L'�l�vation finale du point test� (z) est la valeur la plus petite entre son �l�vation actuelle et l'�l�vation du point pr�c�dent (prev_z)
                newz = dem.getValue(currentrow, currentcol)
            else:
                # Si on a atteint une confluence, on continue jusqu'� ce que qu'on atteingne un point plus bas
                newz = Result.getValue(currentrow, currentcol)
                if newz <= prev_z:
                    intheraster = False

            z = min (prev_z, newz)
            Result.setValue(currentrow, currentcol, z)
            prev_z = z

            # On cherche le prochain point � partir du flow direction
            direction = flowdir.getValue(currentrow, currentcol)
            if (direction == 1):
                currentcol = currentcol + 1

            if (direction == 2):
                currentcol = currentcol + 1
                currentrow = currentrow + 1

            if (direction == 4):
                currentrow = currentrow + 1

            if (direction == 8):
                currentcol = currentcol - 1
                currentrow = currentrow + 1

            if (direction == 16):
                currentcol = currentcol - 1

            if (direction == 32):
                currentcol = currentcol - 1
                currentrow = currentrow - 1

            if (direction == 64):
                currentrow = currentrow - 1

            if (direction == 128):
                currentcol = currentcol + 1
                currentrow = currentrow - 1

            # Tests de s�curit� pour s'assurer que l'on ne sorte pas des rasters
            if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
                intheraster = False
            elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                            flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow, currentcol) <> 8 and
                            flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
                intheraster = False

            if intheraster:
                if (Result.getValue(currentrow, currentcol) <> -255):
                    # Atteinte d'un confluent
                    confluence = True




    Result.save()


    return