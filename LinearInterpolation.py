# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Juillet 2018 - Création


import arcpy
from RasterIO import *



class pointflowpath:
   pass


def execute_LinearInterpolation(r_flowdir, str_frompoint, r_values, str_results, messages, language= "FR"):



    # Chargement des fichiers
    flowdir = RasterIO(r_flowdir)
    bkfatcs = RasterIO(r_values)
    try:
        flowdir.checkMatch(bkfatcs)
    except Exception as e:
        messages.addErrorMessage(e.message)

    Result = RasterIO(r_flowdir, str_results, float,-255)


    # Décompte du nombre de points de départ pour configurer de la barre de progression
    count = 0
    frompointcursor = arcpy.da.SearchCursor(str_frompoint, "OID@")
    for frompoint in frompointcursor:
        count += 1
    progtext = "Traitement"
    if language == "EN":
        progtext = "Processing"
    arcpy.SetProgressor("step", progtext, 0, count, 1)
    progres = 0

    # Traitement effectué pour chaque point de départ
    frompointcursor = arcpy.da.SearchCursor(str_frompoint, ["OID@", "SHAPE@"])
    for frompoint in frompointcursor:
        # Mise à jour de la barre de progression
        arcpy.SetProgressorPosition(progres)
        progres += 1

        # On prend l'objet géométrique (le point) associé à la ligne dans la table
        frompointshape = frompoint[1].firstPoint

        # Conversion des coordonnées
        currentcol = flowdir.XtoCol(frompointshape.X)
        currentrow = flowdir.YtoRow(frompointshape.Y)

        intheraster = True
        # Tests de sécurité pour s'assurer que le point de départ est à l'intérieurs des rasters
        if currentcol<0 or currentcol>=flowdir.raster.width or currentrow<0 or currentrow>= flowdir.raster.height:
            intheraster = False
        elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                            flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow, currentcol) <> 8 and
                            flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
            intheraster = False


        listpointsflowpath = []
        listdistance = []
        listelevation = []
        totaldistance = 0
        currentdistance = 0
        confluence = False

        # Traitement effectué sur chaque cellule le long de l'écoulement
        while (intheraster):

            currentpoint = pointflowpath()
            currentpoint.row = currentrow
            currentpoint.col = currentcol
            totaldistance = totaldistance + currentdistance

            currentpoint.flowlength = totaldistance
            currentpoint.oncs = False


            # On crée une liste des points d'élévation connue le long de l'écoulement, ainsi qu'une liste associée avec leur distance depuis le point de distance
            if bkfatcs.getValue(currentrow, currentcol) <> bkfatcs.nodata:
                if confluence:
                    # point après atteinte d'une confluence. On arrête le traitement
                    intheraster = False
                listdistance.append(totaldistance)
                listelevation.append(bkfatcs.getValue(currentrow, currentcol))
                currentpoint.oncs = True

            currentpoint.previouscsid = len(listdistance) - 1
            if not confluence:
                listpointsflowpath.append(currentpoint)

            # On cherche le prochain point à partir du flow direction
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

            # Tests de sécurité pour s'assurer que l'on ne sorte pas des rasters
            if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
                intheraster = False
            elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                            flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow, currentcol) <> 8 and
                            flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
                intheraster = False

            if intheraster:
                if (Result.getValue(currentrow, currentcol) <> -255):
                    # Atteinte d'un confluent
                    # On continue encore jusqu'au prochain point
                    confluence = True

        if len(listdistance) <= 1:
            # Avertissement si il n'y a qu'un seul (ou aucun) point de données
            if language == "FR":
                messages.addWarningMessage("Point source {0}: pas assez de sections transversales".format(frompoint[0]))
            else:
                messages.addWarningMessage("From point {0}: not enough cross-sections".format(frompoint[0]))

        else:

            currentpointnumber = 0
            # Traitement pour chaque point le long de l'écoulement
            for currentpoint in listpointsflowpath:

                try:
                    if currentpoint.previouscsid == -1:
                        # cas particulier des premiers points avant une cs
                        # on prends la valeur de la premier cs
                        finalvalue = listelevation[0]
                    else:
                        if currentpoint.oncs:
                            # cas particulier : points sur une section transversale
                            finalvalue = listelevation[currentpoint.previouscsid]
                        else:
                            finalvalue = listelevation[currentpoint.previouscsid]* \
                                         (listdistance[currentpoint.previouscsid + 1] - currentpoint.flowlength)/\
                                         (listdistance[currentpoint.previouscsid+1]-listdistance[currentpoint.previouscsid])\
                                         + listelevation[currentpoint.previouscsid+1]* \
                                         (currentpoint.flowlength - listdistance[currentpoint.previouscsid])/\
                                         (listdistance[currentpoint.previouscsid+1]-listdistance[currentpoint.previouscsid])
                except IndexError:
                    # IndexError lorsque l'on est en aval de la dernière section transversales
                    finalvalue = listelevation[-1]

                Result.setValue(currentpoint.row, currentpoint.col, finalvalue)

                currentpointnumber = currentpointnumber + 1


    Result.save()


    return