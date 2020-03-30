# coding: latin-1

#####################################################
# Gu�nol� Chon�
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
# Mars 2017
#####################################################

# v1.4 - Octobre 2019 - Input des d�bits � la limite de la tuile (v1.1, v1.2, v1.3) abandonn�.
#       Retour � la v1.0 + Ajout du d�bit manquant lors d'une confluence + Valeurs par d�faut + Ajout Minslope (au lieu de max) + Suppression param lacs
# v1.5 - Octobre 2019 - version modifi�e pour simulations de l'amont vers l,aval avec reprise de l'�l�vation aval comme condition limite:
# v1.6 - Octobre 2019 - D�bits ajust�s jusqu'� la fin de la zone


import os

from RasterIO import *


class pointflowpath:
   pass

class DefBciWithLateralWlakes_hdown(object):
    def __init__(self):

        self.label = "D�finition des conditions aux limites, H_DOWN"
        self.description = "D�finition des conditions aux limites, H_DOWN"
        self.canRunInBackground = False

    def getParameterInfo(self):


        param_flowdir = arcpy.Parameter(
            displayName="Flow direction",
            name="flowdir",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_discharge = arcpy.Parameter(
            displayName="D�bits",
            name="discharge",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_frompoint = arcpy.Parameter(
            displayName="Points de d�part",
            name="frompoint",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_dist = arcpy.Parameter(
            displayName="Largeur de sortie (m)",
            name="distance",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param_percent = arcpy.Parameter(
            displayName="Pourcentage de correction des d�bits",
            name="percentdischarge",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_zones = arcpy.Parameter(
            displayName="Dossier des zones",
            name="zones",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        param_dist.value = 4000

        param_percent.value = 1

        params = [param_flowdir, param_discharge, param_frompoint, param_dist, param_percent, param_zones]

        return params

    def isLicensed(self):

        return True

    def updateParameters(self, parameters):

        return

    def updateMessages(self, parameters):

        return

    def execute(self, parameters, messages):


        # R�cup�ration des param�tres
        str_flowdir = parameters[0].valueAsText
        str_discharge = parameters[1].valueAsText

        str_frompoint = parameters[2].valueAsText
        distoutput = int(parameters[3].valueAsText)
        percent = float(parameters[4].valueAsText)
        str_zonesfolder = parameters[5].valueAsText

        save_inbci = str_zonesfolder + "\\inbci.shp"
        save_outbci = str_zonesfolder + "\\outbci.shp"
        str_segments = str_zonesfolder + "\\segments"


        # Chargement des fichiers
        flowdir = RasterIO(arcpy.Raster(str_flowdir))
        discharge = RasterIO(arcpy.Raster(str_discharge))
        segments= RasterIO(arcpy.Raster(str_segments))



        try:
            segments.checkMatch(flowdir)
            segments.checkMatch(discharge)

        except Exception as e:
            messages.addErrorMessage(e.message)


        # Listes des points source et des points de sortie
        listinputpoints = []
        listoutputpoints = []

        ### D�but de traitement pour la d�tection des points source principaux ###
        ### Les points source sont plac� au d�but des segments ####

        # donepoint est un dictionnaire de dictionnaires : la premi�re cl� est le num�ro de ligne, la deuxi�me le num�ro de colonne.
        # La seule valeur enregistr�e est True (pourrait �tre optimis� sous une autre forme).
        # Sert pour la d�tection des confluents trait�s
        donepoints = {}

        # Traitement effectu� pour chaque point de d�part
        frompointcursor = arcpy.da.SearchCursor(str_frompoint, ["SHAPE@", "OID@"])
        for frompoint in frompointcursor:

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
                                flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
                intheraster = False


            prevseg = 0
            newfrompoint = True

            # Traitement effectu� pour chaque point le long de l'�coulement
            while (intheraster):

                # Si le point n'est pas enregistr� comme un point trait� dans le dictionnaire donepoints, on l'ajoute
                if currentrow not in donepoints:
                    donepoints.update({currentrow:{}})
                donepoints[currentrow].update({currentcol: True})



                # Lorsqu'on atteint le d�but d'un nouveau segment, on enregistre un nouveau point source
                segmentvalue = segments.getValue(currentrow, currentcol)
                if (newfrompoint or prevseg <> segmentvalue) and segmentvalue<>segments.nodata:
                    newpoint = pointflowpath()
                    newpoint.type = "main"
                    newpoint.frompointid = frompoint[1]
                    # Coordonn�es du point source
                    newpoint.X = flowdir.ColtoX(currentcol)
                    newpoint.Y = flowdir.RowtoY(currentrow)
                    # num�ro de zone
                    newpoint.numzone = segments.getValue(currentrow, currentcol)

                    listinputpoints.append(newpoint)
                    newfrompoint = False



                prevseg = segmentvalue

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


                if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
                    intheraster = False
                elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                                flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow, currentcol) <> 8 and
                                flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
                    intheraster = False

                if intheraster:
                    if currentrow in donepoints:
                        if currentcol in donepoints[currentrow]:
                            # Atteinte d'un confluent
                            intheraster = False


        ### Fin de traitement pour la d�tection des points source principaux ###


        ### D�but de traitement pour la d�tection des points de sortie et des points sources lat�raux ###

        # D�terminer des HFIX pr�d�termin�s (lacs)
        zonescursor = arcpy.da.SearchCursor(str_zonesfolder + "\\buff_segments.shp", ["GRID_CODE", "Z"])
        hfix = {}
        for row in zonescursor:
            hfix[row[0]] = row[1]

        listlateralinputpoints = []

        # Pour chaque raster, on parcourt l'�coulement � partir du point source
        for mainpoint in listinputpoints:



            # Raster de la zone correspondante au point source
            localraster = RasterIO(arcpy.Raster(str_zonesfolder + r"\zone" + str(mainpoint.numzone)))

            # Conversion des coordonn�es
            currentcol = flowdir.XtoCol(mainpoint.X)
            currentrow = flowdir.YtoRow(mainpoint.Y)
            localcol = localraster.XtoCol(mainpoint.X)
            localrow = localraster.YtoRow(mainpoint.Y)

            currentdischarge = discharge.getValue(currentrow, currentcol)
            mainpoint.discharge = currentdischarge
            lastdischarge = currentdischarge

            # Parcours de l'�coulement
            intheraster = True
            while (intheraster):

                prevcol = currentcol
                prevrow = currentrow

                currentdischarge = discharge.getValue(currentrow, currentcol)
                segmentvalue = segments.getValue(currentrow, currentcol)

                if 100. * float(currentdischarge - lastdischarge) / float(
                        lastdischarge) >= percent and segmentvalue <> segments.nodata:
                    newpoint = pointflowpath()
                    newpoint.type = "lateral"
                    newpoint.frompointid = mainpoint.frompointid
                    # Coordonn�es du point source
                    newpoint.X = flowdir.ColtoX(currentcol)
                    newpoint.Y = flowdir.RowtoY(currentrow)
                    # Raster de la zone
                    newpoint.numzone = mainpoint.numzone
                    # Valeur du flow accumulation
                    newpoint.discharge = currentdischarge
                    lastdischarge = currentdischarge

                    listlateralinputpoints.append(newpoint)

                # On cherche le prochain point � partir du flow direction
                direction = flowdir.getValue(currentrow, currentcol)
                if (direction == 1):
                    currentcol = currentcol + 1
                    localcol += 1
                if (direction == 2):
                    currentcol = currentcol + 1
                    currentrow = currentrow + 1
                    localcol += 1
                    localrow += 1

                if (direction == 4):
                    currentrow = currentrow + 1
                    localrow += 1

                if (direction == 8):
                    currentcol = currentcol - 1
                    currentrow = currentrow + 1
                    localcol -= 1
                    localrow += 1

                if (direction == 16):
                    currentcol = currentcol - 1
                    localcol -= 1

                if (direction == 32):
                    currentcol = currentcol - 1
                    currentrow = currentrow - 1
                    localcol -= 1
                    localrow -= 1

                if (direction == 64):
                    currentrow = currentrow - 1
                    localrow -= 1

                if (direction == 128):
                    currentcol = currentcol + 1
                    currentrow = currentrow - 1
                    localcol += 1
                    localrow -= 1

                if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
                    intheraster = False
                elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow,
                                                                                         currentcol) <> 2 and
                              flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow,
                                                                                                 currentcol) <> 8 and
                              flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow,
                                                                                                  currentcol) <> 32 and flowdir.getValue(
                    currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
                    intheraster = False
                if localraster.getValue(localrow, localcol) == localraster.nodata:
                    intheraster = False


            # On enregistre un point de sortie au dernier point trait� avant de sortir de la zone
            newpoint = pointflowpath()
            newpoint.numzone = mainpoint.numzone
            newpoint.X = flowdir.ColtoX(prevcol)
            newpoint.Y = flowdir.RowtoY(prevrow)



            # Il est n�cessaire d'enregistrer le c�t� du raster par lequel on sort.
            # Ceci est fait en regardant la distance entre le dernier point trait� et les coordonn�es maximales de la zone
            # Le c�t� de sortie est le c�t� pour lequel cette distance est minimum
            distside = min(newpoint.X - localraster.raster.extent.XMin, localraster.raster.extent.XMax - newpoint.X, newpoint.Y - localraster.raster.extent.YMin,
                           localraster.raster.extent.YMax - newpoint.Y)
            if distside == newpoint.X - localraster.raster.extent.XMin:
                newpoint.side = "W"
            if distside == localraster.raster.extent.XMax - newpoint.X:
                newpoint.side = "E"
            if distside == newpoint.Y - localraster.raster.extent.YMin:
                newpoint.side = "S"
            if distside == localraster.raster.extent.YMax - newpoint.Y:
                newpoint.side = "N"
            listoutputpoints.append(newpoint)

        listinputpoints.extend(listlateralinputpoints)
        ### Fin de traitement pour la d�tection des points de sortie et des points sources lat�raux ###


        ### D�but de traitement pour la configuration des fen�tres de sortie ###

        # Pour chaque point de sortie
        for point in listoutputpoints:
            raster = RasterIO(arcpy.Raster(str_zonesfolder + r"\zone" + str(point.numzone)))
            colinc = 0
            rowinc = 0
            distinc = 0
            point.side2 = "0"
            point.lim3 = 0
            point.lim4 = 0
            # Selon le cot� de sortie, on progressera horizontalement ou verticalement
            if point.side == "W" or point.side == "E":
                rowinc = 1
                distinc = raster.raster.meanCellHeight
            else:
                colinc = 1
                distinc = raster.raster.meanCellWidth
            currentcol = raster.XtoCol(point.X)
            currentrow = raster.YtoRow(point.Y)
            distance = 0
            # On progresse sur dans une direction jusqu'� sortir du raster ou jusqu'� ce que la distance voullue soit attente
            while raster.getValue(currentrow,currentcol) <> raster.nodata and distance < distoutput/2:
                distance += distinc
                currentrow += rowinc
                currentcol += colinc
            # On prends les coordonn�es avant de sortir du raster
            currentrow -= rowinc
            currentcol -= colinc
            if point.side == "W" or point.side == "E":
                point.lim1 = raster.RowtoY(currentrow)
            else:
                point.lim1 = raster.ColtoX(currentcol)
            # Si la proc�dure s'est arr�t�e parce qu'on est sorti du raster, on tourne de 90 degr�s et on continue
            if distance < distoutput / 2:
                distance -= distinc
                if point.side == "W":
                    colinc = 1
                    rowinc = 0
                    distinc = raster.raster.meanCellWidth
                    point.lim3 = raster.raster.extent.XMin + (currentcol + 0.5) * raster.raster.meanCellWidth
                elif point.side == "E":
                    colinc = -1
                    rowinc = 0
                    distinc = raster.raster.meanCellWidth
                    point.lim3 = raster.raster.extent.XMin + (currentcol + 0.5) * raster.raster.meanCellWidth

                elif point.side == "N":
                    rowinc = 1
                    colinc = 0
                    distinc = raster.raster.meanCellHeight
                    point.lim3 = max(raster.raster.extent.YMin, raster.raster.extent.YMax - (currentrow + 1) * raster.raster.meanCellHeight) + 0.5 * raster.raster.meanCellHeight
                elif point.side == "S":
                    rowinc = -1
                    colinc = 0
                    distinc = raster.raster.meanCellHeight
                    point.lim3 = max(raster.raster.extent.YMin, raster.raster.extent.YMax - (currentrow + 1) * raster.raster.meanCellHeight) + 0.5 * raster.raster.meanCellHeight
                # On progresse � nouveau jusqu'� sortir du raster ou jusqu'� ce que la distance voullue soit attente
                while raster.getValue(currentrow, currentcol) <> raster.nodata and distance < distoutput / 2:
                    distance += distinc
                    currentrow += rowinc
                    currentcol += colinc
                currentrow -= rowinc
                currentcol -= colinc
                # On cherche sur quel cot� on est apr�s avoir tourn� de 90 degr�s
                if point.side == "W" or point.side == "E":
                    point.side2 = "S"
                    point.lim4 = raster.raster.extent.XMin + (currentcol + 0.5) * raster.raster.meanCellWidth
                else:
                    point.side2 = "E"
                    point.lim4 = max(raster.raster.extent.YMin, raster.raster.extent.YMax - (currentrow + 1) * raster.raster.meanCellHeight) + 0.5 * raster.raster.meanCellHeight

            # On recommence toute la proc�dure de l'autre c�t� du point de sortie
            colinc = 0
            rowinc = 0
            distinc = 0
            if point.side == "W" or point.side == "E":
                rowinc = -1
                distinc = raster.raster.meanCellHeight
            else:
                colinc = -1
                distinc = raster.raster.meanCellWidth
            currentcol = raster.XtoCol(point.X)
            currentrow = raster.YtoRow(point.Y)
            distance = 0
            while raster.getValue(currentrow, currentcol) <> raster.nodata and distance < distoutput / 2:
                distance += distinc
                currentrow += rowinc
                currentcol += colinc
            currentrow -= rowinc
            currentcol -= colinc
            if point.side == "W" or point.side == "E":
                point.lim2 = max(raster.raster.extent.YMin, raster.raster.extent.YMax - (currentrow + 1) * raster.raster.meanCellHeight) + 0.5 * raster.raster.meanCellHeight
            else:
                point.lim2 = raster.raster.extent.XMin + (currentcol + 0.5) * raster.raster.meanCellWidth
            # Si la proc�dure s'est arr�t�e parce qu'on est sorti du raster, on tourne de 90 degr�s et on continue
            if distance < distoutput / 2:
                distance -= distinc
                if point.side == "W":
                    colinc = 1
                    rowinc = 0
                    distinc = raster.raster.meanCellWidth
                    point.lim3 = raster.raster.extent.XMin + (currentcol + 0.5) * raster.raster.meanCellWidth
                elif point.side == "E":
                    colinc = -1
                    rowinc = 0
                    distinc = raster.raster.meanCellWidth
                    point.lim3 = raster.raster.extent.XMin + (currentcol + 0.5) * raster.raster.meanCellWidth
                elif point.side == "N":
                    rowinc = 1
                    colinc = 0
                    distinc = raster.raster.meanCellHeight
                    point.lim3 = max(raster.raster.extent.YMin, raster.raster.extent.YMax - (currentrow + 1) * raster.raster.meanCellHeight) + 0.5 * raster.raster.meanCellHeight
                elif point.side == "S":
                    rowinc = -1
                    colinc = 0
                    distinc = raster.raster.meanCellHeight
                    point.lim3 = max(raster.raster.extent.YMin, raster.raster.extent.YMax - (currentrow + 1) * raster.raster.meanCellHeight) + 0.5 * raster.raster.meanCellHeight
                while raster.getValue(currentrow, currentcol) <> raster.nodata and distance < distoutput / 2:
                    distance += distinc
                    currentrow += rowinc
                    currentcol += colinc
                currentrow -= rowinc
                currentcol -= colinc
                if point.side == "W" or point.side == "E":
                    point.side2 = "N"
                    point.lim4 = raster.raster.extent.XMin + (currentcol + 0.5) * raster.raster.meanCellWidth
                else:
                    point.side2 = "W"
                    point.lim4 = max(raster.raster.extent.YMin, raster.raster.extent.YMax - (currentrow + 1) * raster.raster.meanCellHeight) + 0.5 * raster.raster.meanCellHeight

        ### Fin du traitement pour la configuration des fen�tres de sortie ###


        # Cr�ation des shapefiles inbci et outbci, avec les champs n�cessaires
        arcpy.CreateFeatureclass_management(os.path.dirname(save_inbci),
                                            os.path.basename(save_inbci), "POINT", spatial_reference = str_flowdir)
        arcpy.AddField_management(save_inbci, "zone", "TEXT")
        arcpy.AddField_management(save_inbci, "discharge", "FLOAT")
        arcpy.AddField_management(save_inbci, "type", "TEXT")
        arcpy.AddField_management(save_inbci, "fpid", "LONG")
        arcpy.CreateFeatureclass_management(os.path.dirname(save_outbci),
                                            os.path.basename(save_outbci), "POINT", spatial_reference=str_flowdir)
        arcpy.AddField_management(save_outbci, "zone", "TEXT")
        arcpy.AddField_management(save_outbci, "side", "TEXT", field_length=1)
        arcpy.AddField_management(save_outbci, "lim1", "LONG")
        arcpy.AddField_management(save_outbci, "lim2", "LONG")
        arcpy.AddField_management(save_outbci, "side2", "TEXT", field_length=1, )
        arcpy.AddField_management(save_outbci, "lim3", "LONG")
        arcpy.AddField_management(save_outbci, "lim4", "LONG")
        arcpy.AddField_management(save_outbci, "ws", "FLOAT")

        # Enregistrement dans les shapefiles des informations contenues dans les listes
        pointcursor = arcpy.da.InsertCursor(save_inbci, ["zone", "discharge", "type", "fpid", "SHAPE@XY"])
        for point in listinputpoints:
            pointcursor.insertRow([r"zone" + str(point.numzone), point.discharge, point.type, point.frompointid, (point.X, point.Y)])
        pointcursor = arcpy.da.InsertCursor(save_outbci, ["zone", "side", "lim1", "lim2", "side2", "lim3", "lim4", "ws", "SHAPE@XY"])
        for point in listoutputpoints:
            pointcursor.insertRow([r"zone" + str(point.numzone), point.side, point.lim1, point.lim2, point.side2, point.lim3, point.lim4, hfix[point.numzone],(point.X, point.Y)])

        del pointcursor






        return