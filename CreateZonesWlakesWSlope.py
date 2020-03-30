# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
# Fevrier 2019
#####################################################

# v1.1 - 10 mai 2018 - Correction des problèmes de zones dupliquées aux confluences (due aux segments d'un pixel de
#   long). Correction des longueurs des segments aux confluences.
# v1.2 - 28 février 2019 - Suppression des coupures aux confluences, ajout des coupures aux lacs.
# v1.3 - septembre 2019 - Coupure nette des rasters aux lacs + ajout du critère de pente
# v1.4 - octobre 2019 - Debug : problème de coupure des lacs avec multi fp, problème si zone de lac trop courte
# v1.5 - fevrier 2020 - Debug : problème de clip pour les confluent des segments coupé par les lacs

from RasterIO import *

class pointflowpath:
   pass

class CreateZonesWlakes(object):
    def __init__(self):

        self.label = "Découpage en zones, sans les lacs"
        self.description = "Découpage en zones, sans les lacs"
        self.canRunInBackground = False

    def getParameterInfo(self):


        param_flowdir = arcpy.Parameter(
            displayName="Flow direction",
            name="flowdir",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param_dem = arcpy.Parameter(
            displayName="MNE",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_lakes = arcpy.Parameter(
            displayName="Lacs et reservoirs",
            name="lakes",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_slope = arcpy.Parameter(
            displayName="Pente",
            name="slope",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_minslope = arcpy.Parameter(
            displayName="Pente minimale",
            name="minslope",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param_frompoint = arcpy.Parameter(
            displayName="Points de départ",
            name="frompoint",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_distance = arcpy.Parameter(
            displayName="Longueur des segments (m)",
            name="distance",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param_bufferw = arcpy.Parameter(
            displayName="Largeur minimale des zones (m)",
            name="bufferw",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param_folder = arcpy.Parameter(
            displayName="Dossier pour les zones",
            name="folder ",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param0.filter.list = ["File System"]
        param0.value = arcpy.env.scratchWorkspace
        param_frompoint.filter.list = ["Point"]
        param_lakes.filter.list = ["POLYGON"]

        param_distance.value = 10000
        param_bufferw.value = 3000
        param_minslope.value = 0.001

        params = [param_flowdir, param_dem, param_lakes, param_slope, param_minslope, param_frompoint, param_distance, param_bufferw, param_folder, param0]

        return params

    def isLicensed(self):

        return True

    def updateParameters(self, parameters):

        return

    def updateMessages(self, parameters):

        return

    def execute(self, parameters, messages):


        # Récupération des paramètres
        str_flowdir = parameters[0].valueAsText
        str_dem = parameters[1].valueAsText
        str_lakes = parameters[2].valueAsText
        str_slope = parameters[3].valueAsText
        minslope = float(parameters[4].valueAsText)
        str_frompoint = parameters[5].valueAsText
        distance = int(parameters[6].valueAsText)
        bufferw = int(parameters[7].valueAsText)
        str_folder = parameters[8].valueAsText

        arcpy.env.scratchWorkspace = parameters[9].valueAsText

        str_segments = str_folder + "\\segments"
        str_linesegments = str_folder + "\\line_segments.shp"
        str_bufferedsegments = str_folder + "\\buff_segments.shp"


        str_r_lakes = str_folder + "\\r_lakes"

        flowdir = RasterIO(arcpy.Raster(str_flowdir))
        dem = RasterIO(arcpy.Raster(str_dem))
        slope = RasterIO(arcpy.Raster(str_slope))

        try:
            flowdir.checkMatch(dem)
            flowdir.checkMatch(slope)

        except Exception as e:
            messages.addErrorMessage(e.message)

        # Conversion des lacs en raster et copie
        arcpy.env.snapRaster = dem.raster
        arcpy.env.outputCoordinateSystem = dem.raster.spatialReference
        arcpy.PolygonToRaster_conversion(str_lakes, "Z", str_r_lakes+"tmp", cellsize = dem.raster)
        arcpy.Clip_management(str_r_lakes+"tmp", "#", str_r_lakes, dem.raster,"#", "NONE", "MAINTAIN_EXTENT")
        arcpy.Delete_management(str_r_lakes+"tmp")
        lakes = RasterIO(arcpy.Raster(str_r_lakes))
        arcpy.CopyFeatures_management(str_lakes, str_folder + "\\lakes.shp")
        str_lakes = str_folder + "\\lakes.shp"
        arcpy.AddGeometryAttributes_management(str_lakes, "EXTENT")

        ### Début du traitement perrmettant d'identifier les segments (sous forme de raster) ###

        raster_segments = RasterIO(arcpy.Raster(str_flowdir), str_segments, int,-255)

        # numérotation des segments
        segnumber = 0
        toclip = {}

        # Pour chaque point de départ
        frompointcursor = arcpy.da.SearchCursor(str_frompoint, "SHAPE@")
        for frompoint in frompointcursor:

            # On prend l'objet géométrique (le point) associé à la ligne dans la table
            frompointshape = frompoint[0].firstPoint

            # Nouvelle rivière : on change de segment
            segnumber += 1

            # Conversion des coordonnées
            currentcol = flowdir.XtoCol(frompointshape.X)
            currentrow = flowdir.YtoRow(frompointshape.Y)

            # Tests de sécurité pour s'assurer que le point de départ est à l'intérieurs des rasters
            intheraster = True
            if currentcol<0 or currentcol>=flowdir.raster.width or currentrow<0 or currentrow>= flowdir.raster.height:
                intheraster = False
            elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                                flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow, currentcol) <> 8 and
                                flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
                intheraster = False


            listpointsflowpath = []
            totaldistance = 0
            currentdistance = 0
            inlake = True
            # True si la rivière (depuis le point de départ jusqu'au confluent) est composée d'au moins deux segments
            dividedriver = False
            # listtomerged contient la liste des segments trop courts, qui doivent être fusionnés avec segment précédent
            listtomerged = []



            # Pour chaque cellule en suivant l'écoulement
            while (intheraster):

                waslake = inlake
                # coordX = flowdir.ColtoX(currentcol)
                # coordY = flowdir.RowtoY(currentrow)
                #shplakes = arcpy.SearchCursor(str_lakes)
                inlake = False
                lakevalue = lakes.getValue(currentrow, currentcol)

                inlake = (lakevalue <> lakes.nodata)

                # for shplake in shplakes:
                #     if shplake.Shape.contains(arcpy.Point(coordX, coordY)):
                #         inlake = True


                if not (inlake and waslake):
                    # Distance parcourue depuis le début du segment
                    totaldistance = totaldistance + currentdistance

                # Test si on arrive à un lac
                if inlake and not waslake:
                    # Segment trop court si de longueur inférieure à 30% de la distance voullue
                    # Le segment doit être alors fusionné avec le segment précédent (qui existe uniquement si dividedriver = True)
                    # ajout de l'info de clipper ensuite également
                    coordX = flowdir.ColtoX(currentcol)
                    coordY = flowdir.RowtoY(currentrow)
                    shplakes = arcpy.da.SearchCursor(str_lakes, ["SHAPE@", "EXT_MIN_X", "EXT_MAX_X", "EXT_MIN_Y", "EXT_MAX_Y", "Z"])
                    for shplake in shplakes:
                        if shplake[0].contains(arcpy.Point(coordX, coordY)):
                            distXmin = abs(coordX - shplake[1])
                            distXmax = abs(coordX - shplake[2])
                            distYmin = abs(coordY - shplake[3])
                            distYmax = abs(coordY - shplake[4])
                            mini = min(distXmin, distXmax, distYmin, distYmax)
                            if mini == distXmin:
                                toclip[segnumber] = ["Xmax", shplake[1], shplake[5]]
                                messages.addMessage(str(segnumber)+" Xmax " + str(shplake[1]))
                            if mini == distXmax:
                                toclip[segnumber] = ["Xmin", shplake[2], shplake[5]]
                                messages.addMessage(str(segnumber) + " Xmin " + str(shplake[2]))
                            if mini == distYmin:
                                toclip[segnumber] = ["Ymax", shplake[3], shplake[5]]
                                messages.addMessage(str(segnumber) + " Ymax " + str(shplake[3]))
                            if mini == distYmax:
                                toclip[segnumber] = ["Ymin", shplake[4], shplake[5]]
                                messages.addMessage(str(segnumber) + " Ymin " + str(shplake[4]))
                    if totaldistance < 0.3 * distance and dividedriver:
                        if segnumber in toclip:
                            toclip[segnumber - 1] = toclip.pop(segnumber)
                        listtomerged.append(segnumber)
                    totaldistance = 0
                    segnumber += 1
                    dividedriver = False


                elif totaldistance > distance and slope.getValue(currentrow,currentcol) > minslope:
                    # Test si on a parcouru la distance voullue
                    totaldistance = 0
                    segnumber += 1
                    dividedriver = True

                if not inlake:
                    # On conseerve une liste des points traités, avec leur numéro de segment
                    currentpoint = pointflowpath()
                    currentpoint.row = currentrow
                    currentpoint.col = currentcol
                    currentpoint.distance = totaldistance
                    currentpoint.segnumber = segnumber
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
                    confluence_seg = raster_segments.getValue(currentrow, currentcol)
                    if (confluence_seg <> -255):
                        # Atteinte d'un confluent déjà traité

                        # Si le segment dans lequel on arrive est limité par un lac, le confluent peut l'être aussi
                        # On copie l'item toclip pour limiter l'étendu de la zone
                        # par contre on garde l'élévation à -999 (hfix sera le résultat de la simulation du cours d'eau confluent)
                        if confluence_seg in listtomerged:
                            confluence_seg -= 1
                        if confluence_seg in toclip:
                            clipitem = list(toclip[confluence_seg])
                            clipitem[2] = -999
                            toclip[segnumber] = clipitem


                        if totaldistance < 0.3 * distance and dividedriver:
                            # Segment trop court si de longueur inférieure à 30% de la distance voullue
                            # Le segment doit être alors fusionné avec le segment précédent (qui existe uniquement si dividedriver = True)
                            listtomerged.append(segnumber)
                            if segnumber in toclip:
                                toclip[segnumber - 1] = toclip.pop(segnumber)



                        intheraster = False






            # Pour chaque point traité le long de l'écoulement
            for currentpoint in listpointsflowpath:
                # Si c'est un point d'un segment trop court, on remplace le numéro du segment par le numéro du segment précédent
                if currentpoint.segnumber in listtomerged:
                    currentpoint.segnumber -= 1
                # On enregistre le point
                raster_segments.setValue(currentpoint.row, currentpoint.col,
                                currentpoint.segnumber)

        raster_segments.save()

        ### Fin du traitement perrmettant d'identifier les segments ###


        ### Transformation du raster des segments en zones ####

        # Transformation en polyline
        scratchfolder = arcpy.env.scratchWorkspace
        tmp_segments = scratchfolder + "\\tmpsegments.shp"
        arcpy.RasterToPolyline_conversion(str_segments,tmp_segments)
        arcpy.Dissolve_management(tmp_segments,str_linesegments,"GRID_CODE")
        arcpy.Delete_management(tmp_segments)
        # Création de la zone tampon
        arcpy.Buffer_analysis(str_linesegments,str_bufferedsegments,bufferw)

        # Suppression des lacs
        #arcpy.Erase_analysis(str_bufferedsegments, str_lakes, str_bufferedsegments2)


        # Création de la zone pour chaque segment
        arcpy.AddField_management(str_bufferedsegments, "Z", "FLOAT")
        segmentscursor = arcpy.da.UpdateCursor(str_bufferedsegments, ["GRID_CODE", "SHAPE@", "Z"])
        for segment in segmentscursor:
            Xmin = segment[1].extent.XMin
            Ymin = segment[1].extent.YMin
            Xmax = segment[1].extent.XMax
            Ymax = segment[1].extent.YMax
            if segment[0] in toclip:
                segment[2] = toclip[segment[0]][2]
                if toclip[segment[0]][0] == "Xmin":
                    Xmin = max(toclip[segment[0]][1], Xmin)
                if toclip[segment[0]][0] == "Xmax":
                    Xmax = min(toclip[segment[0]][1], Xmax)
                if toclip[segment[0]][0] == "Ymin":
                    Ymin = max(toclip[segment[0]][1], Ymin)
                if toclip[segment[0]][0] == "Ymax":
                    Ymax = min(toclip[segment[0]][1], Ymax)
            else:
                segment[2] = -999
            segmentscursor.updateRow(segment)


            envelope = str(Xmin)+" "+str(Ymin)+" "+str(Xmax)+" "+str(Ymax)
            arcpy.Clip_management(dem.raster, envelope, str_folder + "\\zone" + str(segment[0]))

        return





