# -*- coding: utf-8 -*-

# execute_largeurpartransect by François Larouche-Tremblay, Ing, M Sc

import arcpy
import numpy as np
from os.path import basename
from arcpy import env
from arcpy.lr import LocateFeaturesAlongRoutes, MakeRouteEventLayer
from arcpy.management import AddField, CalculateField, SelectLayerByLocation, MakeFeatureLayer, \
    DeleteIdentical, FeatureVerticesToPoints, JoinField, AlterField, SplitLineAtPoint, CopyFeatures, \
    SelectLayerByAttribute, MultipartToSinglepart, DeleteRows, DeleteField, Merge, PolygonToLine, \
    Dissolve, FeatureToLine, CreateTable, PointsToLine
from arcpy.analysis import Intersect, Buffer, Statistics, Erase, Near, CreateThiessenPolygons, SpatialJoin
from arcpy.da import NumPyArrayToTable, TableToNumPyArray, FeatureClassToNumPyArray
from DataManagementDEH import addfieldtoarray, deleteuselessfields, getfieldproperty, ScratchIndex

from tree.RiverNetwork import *
import ArcpyGarbageCollector as gc
import numpy.lib.recfunctions as rfn

def pointsdextremites(streamnetwork, banklines, endpoints):
    # **************************************************************************
    # DÉFINITION :
    # Génère les extrémités des tronçons en excluant les zones de confluence.
    # Les points sont positionnés à une distance approximative d'une
    # demi-largeur de cours d'eau directement en amont ou en aval des confluences.

    # ENTRÉES :
    # streamnetwork = STRING, chemin d'accès vers le réseau de référencement linéaire
    # banklines = STRING, chemin d'accès vers la ligne de contour du
    #                     polygone des cours d'eau.
    # cellsize = FLOAT, largeur des cellules du MNT utilisé pour le pré-traitement
    # enpoints = STRING, emplacement où seront enregistrés les points d'extrémités

    # SORTIE :
    # enpoints = STRING, les points d'extrémités des branches sont enregistrés.
    # **************************************************************************

    gc = ScratchIndex()  # Régistre des couches de données temporaires
    try:
        # Création d'un ensemble de points aux extrémités aval des tronçons
        confpts = gc.scratchname("ptex", "FeatureClass", workspace=env.scratchWorkspace)
        FeatureVerticesToPoints(streamnetwork, confpts, "END")
        DeleteIdentical(confpts, ["Shape"])  # Suppression des doublons

        # Suppression des points aval qui ne sont pas des confluences
        dangpts = gc.scratchname("mptex", "FeatureClass")
        FeatureVerticesToPoints(streamnetwork, dangpts, "DANGLE")
        MakeFeatureLayer(confpts, "confpts_lyr")
        SelectLayerByLocation("confpts_lyr", "INTERSECT", dangpts, "", "NEW_SELECTION")
        DeleteRows("confpts_lyr")
        SelectLayerByAttribute("confpts_lyr", "CLEAR_SELECTION")

        # Calcul de la distance des points de confluence avec la berge la plus proche
        Near(confpts, banklines, None, "NO_LOCATION", "NO_ANGLE", "PLANAR")
        AddField(confpts, "Buff_dist", "FLOAT")
        # HARDCODED : Il est préférable de prendre 2 fois le cellsize du MNT utilisé pour le pré-traitement.
        cellsize = 4
        CalculateField(confpts, "Buff_dist", "!NEAR_DIST! + {0}".format(2 * cellsize), "PYTHON3")  # Résolution du MNT

        # Création d'un ensemble de points situés immédiatement en amont ou en aval des points de confluence
        confbuff = gc.scratchname("mptex", "FeatureClass")
        Buffer(confpts, confbuff, "Buff_dist", "FULL", "ROUND", "NONE", "", "PLANAR")

        buffend = gc.scratchname("mptex", "FeatureClass")
        Intersect([confbuff, streamnetwork], buffend, "ALL", "", "POINT")
        MultipartToSinglepart(buffend, endpoints)

    finally:
        # Suppression des couches de données temporaires
        gc.wipeindex()

    return


def pointsdemesure(streamnetwork, idfield, csfield, distfield, typefield, spacing, datapoints, endpoints=None):
    # **************************************************************************
    # DÉFINITION :
    # Génère les extrémités des tronçons en excluant les zones de confluence.
    # Les points sont positionnés à une distance approximative d'une
    # demi-largeur de cours d'eau directement en amont ou en aval des confluences.

    # ENTRÉES :
    # streamnetwork = STRING, chemin d'accès vers le réseau de référencement linéaire
    # idfield = STRING, nom du champ contenant les identifiants de tronçons
    # csfield = STRING, nom du champ qui contiendra un identifiant unique de point (Exemple: "CSid")
    # distfield = STRING, nom du champ qui contiendra la distance par rapport à l'amont (Exemple: "Distance_m")
    # typefield = STRING, nom du champ qui contiendra le type des points, soit:
    #                     CSTYPE : Normal = 1, Confluence = 0, Start = 2, Stop = 3
    # spacing = FLOAT, espacement entre les points de mesure
    # datapoints = STRING, emplacement où seront enregistrés les points de mesure
    # enpoints = STRING, chemin d'accès vers les points d'extrémités

    # offset=0, possibilité d'ajouter un offset pour tester la sensibilité du placement des sections

    # SORTIE :
    # datapoints = STRING, les points de mesure sont enregistrés.
    # **************************************************************************

    sws = env.scratchWorkspace
    gc = ScratchIndex()  # Régistre des couches de données temporaires

    try:
        idln = FeatureClassToNumPyArray(streamnetwork, [idfield, "SHAPE@LENGTH"], null_value=-9999)
        forkid = idln[idfield]
        length = idln["SHAPE@LENGTH"]
        strt = np.zeros(length.shape)
        stop = np.copy(length)
        tips = np.tile(np.array([1, 1, 1, 0]), [length.shape[0], 1])

        # Afin d'exclure les zones de confluence, les points sont générés entre les points d'extrémités (inclus)
        # Si les points d'extrémités ne sont pas spécifiés, les points de mesure sont générés sur toute la longueur.
        if endpoints is not None:
            endevnt = gc.scratchname("ptme", "Table", workspace=sws)
            LocateFeaturesAlongRoutes(endpoints, streamnetwork, idfield, "0.1 Meters", endevnt, "Routeid Point Measure",
                                      "ALL", "NO_DISTANCE", "", "NO_FIELDS", "")
            endarr = TableToNumPyArray(endevnt, ["Routeid", "Measure"], null_value=-9999)
            for i in range(0, forkid.shape[0], 1):
                ends = endarr["Measure"][endarr["Routeid"] == forkid[i]]
                if ends.shape[0] >= 1:
                    strt[i] = np.min(ends)
                    stop[i] = np.max(ends)
            ratio = np.divide(strt, length)
            con1 = np.logical_and(strt == stop, ratio >= 0.5)
            con2 = np.logical_and(strt == stop, ratio < 0.5)
            strt[con1] = 0
            stop[con2] = length[con2]
            tips[strt != 0] = np.array([0, 2, 1, 1])
            tips[stop != length, 2:] = np.array([3, 0])

        # Requête des paramètres du champ idfield
        idft = getfieldproperty(streamnetwork, idfield, "type", default="STRING")
        if idft == "STRING":
            idft = "TEXT"

        # Création des champs dans la table vide
        temptabl = gc.scratchname("ptme", "Table", workspace=sws)
        CreateTable(sws, basename(temptabl))  # Champ OBJECTID créé avec la table
        fieldnames = [csfield, distfield, idfield, typefield]
        for field, dtype in zip(fieldnames, ["LONG", "FLOAT", idft, "LONG"]):
            AddField(temptabl, field, dtype)

        s1arr = TableToNumPyArray(temptabl, fieldnames, null_value=-9999)
        arrlist = []
        trows = 0
        dt1 = s1arr.dtype
        for sa, so, tip, ln, fkid in zip(strt, stop, tips, length, forkid):
            arcpy.AddMessage("La branche {0} commence à {1}, finit à {2}, a une longueur de {3}.".format(fkid, sa, so, ln))

            if (so - sa) < 0:
                arcpy.AddMessage("La branche {0} est trop courte, elle ne peut être traitée.".format(fkid))
                continue

            if (so - sa) < (3 * spacing):
                dist = np.arange(sa, so + 0.0001, (so - sa)/3)  # Position par rapport à l'amont de la branche

                arcpy.AddMessage("La branche {0} est courte, l'espacement ne sera pas respecté.".format(fkid))
                # continue
            else:
                dist = np.arange(sa, so, spacing)  # Position par rapport à l'amont de la branche de chaque transect

            if (so - dist[-1]) > (spacing / 2):  # Dernier transect déplacé ou ajouté
                dist = np.append(dist, so)
            else:
                dist[-1] = so

            if sa != 0:  # Si la CS amont n'est pas à la confluence, on ajoute un point
                dist = np.append([0], dist)

            if so != ln:  # Si la CS aval n'est pas à la confluence, on ajoute un point
                dist = np.append(dist, [ln])

            nrows = dist.shape[0]
            trows += nrows
            newblock = np.repeat(np.array([(0, 0, fkid, 0)], dtype=dt1), nrows)
            newblock[distfield] = dist

            newblock[typefield] = np.concatenate((tip[:2], np.repeat(1, nrows - 4), tip[2:]))  # Assignation du CSType
            arrlist.append(newblock)

        s1arr = np.concatenate(arrlist)
        s1arr[csfield] = np.arange(1, trows + 1, 1)
        s1evnt = gc.scratchname("ptme", "Table", workspace=sws)
        NumPyArrayToTable(s1arr, s1evnt)
        eventtype = "{0} Point {1}".format(idfield, distfield)
        MakeRouteEventLayer(streamnetwork, idfield, s1evnt, eventtype, "s1evnt_lyr", None)
        CopyFeatures("s1evnt_lyr", datapoints)  # Enregistre les points de repère de distance et le type de chaque CS

    finally:
        # Suppression des couches de données temporaires
        gc.wipeindex()

    return


def transectsauxpointsdemesure(streamnetwork, idfield, cspoints, csfield, distfield, typefield,  maxwidth,
                               riverbanks, transects):
    # **************************************************************************
    # DÉFINITION :
    # Génère des transects rectilignes sur toutes les branches du réseau à
    # chacun des points de mesure fournit en entrée, en excluant les confluences.

    # ENTRÉES :
    # streamnetwork = STRING, chemin d'accès vers le réseau de référencement linéaire
    # idfield = STRING, nom du champ contenant les identifiants de tronçons
    # cspoints = STRING, chemin d'accès vers les points de positionnement des
    #                    transects. Les points doivent contenir un champ qui
    #                    indique le type des transects, soit:
    #                    CSTYPE : Normal = 1, Confluence = 0, Start = 2, Stop = 3
    # csfield = STRING, nom du champ qui contiendra un identifiant unique de point (Exemple: "CSid")
    # distfield = STRING, nom du champ qui contiendra la distance par rapport à l'amont (Exemple: "Distance_m")
    # typefield = STRING, nom du champ qui contient le type de transect
    # maxwidth = FLOAT, largeur maximale des transects
    # riverbanks = STRING, chemin d'accès vers les lignes de berge des cours d'eau; les transects
    #                    seront contenus à l'intérieur des berges
    # transects = STRING, emplacement où seront enregistrés les transects

    # SORTIE :
    # transects = STRING, les transects sont enregistrés sous forme de lignes
    # **************************************************************************
    sws = env.scratchWorkspace
    gc = ScratchIndex()  # Régistre des couches de données temporaires

    try:
        MakeFeatureLayer(cspoints, "cspoints_lyr")
        SelectLayerByAttribute("cspoints_lyr", "NEW_SELECTION", '"{0}" >= 1'.format(typefield), "")

        csarr = TableToNumPyArray("cspoints_lyr", [csfield, idfield, distfield], null_value=-9999)
        csarr = np.sort(csarr, order=csfield)  # Au cas où l'ordre des points aurait été mélangé

        SelectLayerByAttribute("cspoints_lyr", "CLEAR_SELECTION")

        # On ajoute le champ et les valeurs de offset pour générer les évènements de chaque côté du réseau
        ofstfield = "Offset"
        transarr = addfieldtoarray(np.repeat(csarr, 2), (ofstfield, '<f8'))  # Deux points pour chaque transects
        transarr[ofstfield] = np.tile([maxwidth / 2, -maxwidth / 2], csarr.shape[0])

        # Création des transects en reliant les points générés de part et d'autre du réseau de cours d'eau
        transevnt = gc.scratchname("trpt", "Table", workspace=sws)
        NumPyArrayToTable(transarr, transevnt)
        eventtype = "{0} Point {1}".format(idfield, distfield)
        MakeRouteEventLayer(streamnetwork, idfield, transevnt, eventtype, "transevnt_lyr", offset_field=ofstfield)

        rawtrans = gc.scratchname("trpt", "FeatureClass", workspace=sws)
        PointsToLine("transevnt_lyr", rawtrans, csfield, "", "NO_CLOSE")

        transends = gc.scratchname("trpt", "FeatureClass", workspace=sws)
        Intersect([rawtrans, riverbanks], transends, "ONLY_FID", "", "POINT")

        # Découpage des transects brutes en fonction des lignes de berges
        SplitLineAtPoint(rawtrans, transends, transects, "0.05 Meters")
        deleteuselessfields(transects, ["SHAPE_LENGTH", "OBJECTID", "SHAPE"], mapping="FC")

    finally:
        # Suppression des couches de données temporaires
        gc.wipeindex()

    # Sélection des transects et suppression des lignes situés à l'extérieur des lignes de berge
    MakeFeatureLayer(transects, "splitrans_lyr")
    SelectLayerByLocation("splitrans_lyr", "INTERSECT", cspoints, "", "NEW_SELECTION", "INVERT")
    DeleteRows("splitrans_lyr")
    SelectLayerByAttribute("splitrans_lyr", "CLEAR_SELECTION")

    return


def transectsauxconfluences(cspoints, typefield, riverbanks, transects):
    # **************************************************************************
    # DÉFINITION :
    # Génère des transects en forme de pointe aux confluences pour qu'ils soient
    # perpendiculaires à l'écoulement et qu'ils ne dépassent pas dans le confluent.

    # ENTRÉES :
    # cspoints = STRING, chemin d'accès vers les points de positionnement des
    #                    transects. Les points doivent contenir un champ qui
    #                    indique le type des transects, soit:
    #                    CSTYPE : Normal = 1, Confluence = 0, Start = 2, Stop = 3
    # typefield = STRING, nom du champ qui contient le type de transect
    # transects = STRING, emplacement où seront enregistrés les transects

    # SORTIE :
    # transects = STRING, les transects sont enregistrés sous forme de lignes
    # **************************************************************************
    sws = env.scratchWorkspace

    gc = ScratchIndex()  # Régistre des couches de données temporaires

    try:
        MakeFeatureLayer(cspoints, "cspts_lyr")
        SelectLayerByAttribute("cspts_lyr", "NEW_SELECTION", '"{0}" >= 2'.format(typefield))

        thiepoly = gc.scratchname("mtrco", "FeatureClass")
        CreateThiessenPolygons("cspts_lyr", thiepoly, "ALL")

        disspoly = gc.scratchname("mtrco", "FeatureClass")
        Dissolve(thiepoly, disspoly, "CSType", "", "SINGLE_PART", "DISSOLVE_LINES")

        conftrans = gc.scratchname("trco", "FeatureClass", workspace=sws)
        FeatureToLine([disspoly], conftrans, "0.001 Meters", "NO_ATTRIBUTES")

        transends = gc.scratchname("trco", "FeatureClass", workspace=sws)
        Intersect([conftrans, riverbanks], transends, "ONLY_FID", "", "POINT")

        # Découpage des transects brutes en fonction des lignes de berges
        SplitLineAtPoint(conftrans, transends, transects, "0.05 Meters")
        deleteuselessfields(transects, ["SHAPE_LENGTH", "OBJECTID", "SHAPE"], mapping="FC")

    finally:
        # Suppression des couches de données temporaires
        gc.wipeindex()

    # Sélection des transects et suppression des lignes situés à l'extérieur des lignes de berge
    MakeFeatureLayer(transects, "splitrans_lyr")
    SelectLayerByLocation("splitrans_lyr", "INTERSECT", cspoints, "", "NEW_SELECTION", "INVERT")
    DeleteRows("splitrans_lyr")
    SelectLayerByAttribute("splitrans_lyr", "CLEAR_SELECTION")

    return


def transectsverspoints(transects, datapoints):
    # **************************************************************************
    # DÉFINITION :
    # Transfert les données contenues dans la table d'attribut des transects
    # vers les points de mesure

    # ENTRÉES :
    # transects = STRING, chemin d'accès vers les transects (polyline)
    # datapoints = STRING, chemin d'accès vers les points de positionnement des
    #                      transects.
    # tol = STRING, portée (en m) pour le SpatialJoin

    # SORTIE :
    # La table d'attribut des datapoints est modifiée pour y ajouter les données
    # contenues dans les transects. Seuls les points correspondant à des transects
    # sont conservés.
    # **************************************************************************

    gc = ScratchIndex()  # Régistre des couches de données temporaires

    fieldnames = [f.name for f in arcpy.ListFields(datapoints)] + [f.name for f in arcpy.ListFields(transects)]
    fms = arcpy.FieldMappings()  # Table d'attribut suite à l'ajout des extrémités des pré-découpages/confluences
    fms.addTable(transects)

    try:
        oldpts = gc.scratchname("trpt", "FeatureClass", workspace=env.scratchWorkspace)
        CopyFeatures(datapoints, oldpts)

        MakeFeatureLayer(oldpts, "datapts_lyr")
        SelectLayerByLocation("datapts_lyr", "INTERSECT", transects, "0.1 Meters", "NEW_SELECTION")
        fms.addTable("datapts_lyr")

        tol = 1
        # HARDCODED : Portée (en m) pour le SpatialJoin. Puisque les points de mesure sont normalement situés
        # directement sur les transects, une tolérance de 0.5 m est amplement suffisante.
        # Attention, le spacing entre les transects doit être supérieur à la portée.

        SpatialJoin("datapts_lyr", transects, datapoints, "JOIN_ONE_TO_ONE",
                    "KEEP_ALL", fms, "WITHIN_A_DISTANCE", "{0} Meters".format(tol), None)

        deleteuselessfields(datapoints, fieldnames, mapping="FC")

    finally:
        # Suppression des couches de données temporaires
        gc.wipeindex()

    return


def largeurdestransects(streamnetwork, transects, widthfield):
    # **************************************************************************
    # DÉFINITION :
    # Génère des transects équidistants sur chacune des branches du réseau de
    # cours d'eau ainsi que des transects en pointes aux confluences et produit
    # un ensemble de point contenant la largeur des cours d'eau aux transects

    # ENTRÉES :
    # streamnetwork = STRING, chemin d'accès vers le réseau de référencement linéaire
    # idfield = STRING, nom du champ contenant les identifiants de tronçons
    # riverbed = STRING, chemin d'accès vers le polygone des cours d'eau;
    #                    les transects seront contenus dans ce polygone
    # cellsize = FLOAT, largeur des cellules du MNT utilisé pour le pré-traitement
    # maxwidth = FLOAT, largeur maximale des transects
    # spacing = FLOAT, espacement régulier entre les sections (en m)
    # transects = STRING, emplacement où seront enregistrés les transects (Polyline)
    # widthpts = STRING, emplacement où seront enregistrés les points contenant
    #                    la largeur aux transects
    # ineffarea = STRING, chemin d'accès vers les polygones qui masquent
    #                     les zones d'écoulement ineffectives

    # SORTIE :
    # Les couches des transects est des points contenant la largeur aux
    # transects sont enregistrées.
    # **************************************************************************

    # **************************************************************************
    mflag = env.outputMFlag
    sws = env.scratchWorkspace
    gc = ScratchIndex()

    try:
        env.outputMFlag = "Disabled"  # Pour que DeleteIdentical fonctionne aux confluences

        # Nettoyage des transects qui traversent deux chenaux ou plus
        overlaps = gc.scratchname("latr", "FeatureClass", workspace=sws)
        Intersect([transects, streamnetwork], overlaps, "ALL", "", "POINT")

        singols = gc.scratchname("latr", "FeatureClass", workspace=sws)
        MultipartToSinglepart(overlaps, singols)
        DeleteIdentical(singols, ["Shape"])  # Les transects aux confluences génèrent des doublons

        tabletemp = gc.scratchname("tlatr", "Table", workspace=sws)
        fname = "FID_{0}".format(basename(transects))
        Statistics(singols, tabletemp, [["{0}".format(fname), "COUNT"]], fname)

        MakeFeatureLayer(transects, "transects_lyr")
        JoinField("transects_lyr", "OBJECTID", tabletemp, fname, "COUNT_{0}".format(fname))
        AlterField("transects_lyr", "COUNT_{0}".format(fname), "Bad_Ori")
        SelectLayerByAttribute("transects_lyr", "NEW_SELECTION", '"Bad_Ori" >= 2', "")
        desc = arcpy.Describe("transects_lyr")
        if desc.FIDSet != "":
            DeleteRows("transects_lyr")

        SelectLayerByAttribute("transects_lyr", "CLEAR_SELECTION")
        DeleteField(transects, "Bad_Ori")  # On supprime le champ temporaire

    finally:
        # Suppression des couches de données temporaires
        gc.wipeindex()

    # Ajout d'un champ pour le calcul de la largeur
    AddField(transects, widthfield, "FLOAT", field_alias=widthfield, field_is_nullable="NULLABLE")
    CalculateField(transects, widthfield, "!Shape_Length!", "PYTHON3")

    env.outputMFlag = mflag  # L'environnement est remis à son état initial

    return


def supprimercroisements(transects, nx):
    # **************************************************************************
    # DÉFINITION :
    # Boucle de nettoyage des transects mal orientés ou avec trop de croisements
    #
    # ENTREES :
    # transects = STRING, chemin d'accès vers les transects (polyline)
    # nx = INTEGER, nombre de croisements toléré
    #
    # SORTIES :
    # Les transects avec trop de croisements sont supprimés.
    # **************************************************************************
    sws = env.scratchWorkspace
    gc = ScratchIndex()

    try:
        fname = "FID_{0}".format(basename(transects))
        MakeFeatureLayer(transects, "transects_lyr")
        for ii in range(5, nx, -1):
            overlaps = gc.scratchname("msucr", "FeatureClass")
            Intersect("transects_lyr", overlaps, "ONLY_FID", "", "POINT")

            tabletemp = gc.scratchname("sucr", "Table", workspace=sws)
            Statistics(overlaps, tabletemp, [[fname, "COUNT"]], fname)
            JoinField("transects_lyr", "OBJECTID", tabletemp, fname, "COUNT_{0}".format(fname))
            # AlterField("transects_lyr", "COUNT_{0}".format(fname), "Overlap{0:02d}".format(ii))

            # SelectLayerByAttribute("transects_lyr", "NEW_SELECTION", '"Overlap{0:02d}" >= {1}'.format(ii, ii), "")
            SelectLayerByAttribute("transects_lyr", "NEW_SELECTION", '"COUNT_{0}" >= {1}'.format(fname, ii), "")
            desc = arcpy.Describe("transects_lyr")
            if desc.FIDSet != "":
                DeleteRows("transects_lyr")

            SelectLayerByAttribute("transects_lyr", "CLEAR_SELECTION")
            DeleteField("transects_lyr", "COUNT_{0}".format(fname))  # On supprime le champ temporaire

    finally:
        # Suppression des couches de données temporaires
        gc.wipeindex()

    return


def execute_largeurpartransect(streamnetwork, idfield, riverbed, ineffarea, maxwidth, spacing,
                               transects, cspoints, messages):
    # **************************************************************************
    # DÉFINITION :
    # Corps d'exécution (main) de l'outil de calcul de la largeur des cours d'eau.

    # ENTRÉES :
    # streamnetwork = STRING, chemin d'accès vers le réseau de référencement linéaire
    # idfield = STRING, nom du champ contenant les identifiants de tronçons
    # riverbed = STRING, chemin d'accès vers le polygone des cours d'eau;
    #                    les transects seront contenus dans ce polygone
    # ineffarea = STRING, chemin d'accès vers les polygones qui masquent
    #                     les zones d'écoulement ineffectives
    # maxwidth = FLOAT, largeur maximale des transects
    # spacing = FLOAT, espacement régulier entre les sections (en m)
    # transects = STRING, emplacement où seront enregistrés les transects (Polyline)
    # cspoints = STRING, emplacement où seront enregistrés les points contenant
    #                    la largeur aux transects

    # SORTIE :
    # Les couches des transects est des points contenant la largeur aux
    # transects sont enregistrées.
    # **************************************************************************

    # Paramètres d'environnement et de gestion des couches temporaires
    sws = env.scratchWorkspace
    gc = ScratchIndex()

    try:
        # Suppression des zones d'écoulement ineffectives
        if ineffarea and ineffarea != "#":
            effbed = gc.scratchname("mmexlt", "FeatureClass")
            Erase(riverbed, ineffarea, effbed)
            inpoly = effbed
        else:
            inpoly = riverbed

        csfield, distfield, typefield = "CSid", "Distance_m", "CSType"  # HARDCODED

        # Création des lignes des berges de cours d'eau
        riverbanks = gc.scratchname("mexlt", "FeatureClass")
        PolygonToLine(inpoly, riverbanks, "IGNORE_NEIGHBORS")

        # Création d'un ensemble de points situés immédiatement en amont et en aval des points de confluence
        endcs = gc.scratchname("mexlt", "FeatureClass")
        pointsdextremites(streamnetwork, riverbanks, endcs)

        # Création de l'ensemble de points où sera mesurée la largeur sur le réseau (entre les points d'extrémités)
        pointsdemesure(streamnetwork, idfield, csfield, distfield, typefield, spacing, cspoints, endcs)

        # Création des transects équidistants situés sur les branches de cours d'eau
        rawtrans = gc.scratchname("exlt", "FeatureClass", workspace=sws)
        transectsauxpointsdemesure(streamnetwork, idfield, cspoints, csfield, distfield,
                                   typefield, maxwidth, riverbanks, rawtrans)

        # Création des transects en pointe situés aux confluences
        conftrans = gc.scratchname("exlt", "FeatureClass", workspace=sws)
        transectsauxconfluences(cspoints, typefield, riverbanks, conftrans)

        Merge([rawtrans, conftrans], transects)

    finally:
        # Suppression des couches de données temporaires
        gc.wipeindex()

    widthfield = "Largeur_m"  # HARDCODED
    largeurdestransects(streamnetwork, transects, widthfield)

    nx = 2  # Nombre de croisements tolérés
    supprimercroisements(transects, nx)

    transectsverspoints(transects, cspoints)

    return

def execute_WidthPostProc(network_shp, RID_field, main_field, links_table, widthdata, widthid, width_RID_field, width_distance, width_field, widthoutput, messages):
    # - Merge together side-by-side channels
    # - Filter out sudden increases of width


    # network = RiverNetwork()
    # network.dict_attr_fields['id'] = RID_field
    # network.load_data(network_shp, links_table)
    #
    # widthcoll = Points_collection(network, "width")
    # widthcoll.dict_attr_fields['id'] = widthid
    # widthcoll.dict_attr_fields['reach_id']= width_RID_field
    # widthcoll.dict_attr_fields['dist'] = width_distance
    # widthcoll.dict_attr_fields.pop('offset')
    # widthcoll.dict_attr_fields['width'] = width_field
    # widthcoll.load_table(widthdata)

    # Create a layer with only the main channels and one with only the secondary channels
    arcpy.MakeFeatureLayer_management(widthdata, "width_main_lyr")
    arcpy.AddJoin_management("width_main_lyr", width_RID_field, network_shp, RID_field)
    arcpy.SelectLayerByAttribute_management("width_main_lyr", "NEW_SELECTION", os.path.basename(network_shp)+"."+main_field+ " = 1")
    arcpy.MakeFeatureLayer_management(widthdata, "width_second_lyr")
    arcpy.AddJoin_management("width_second_lyr", width_RID_field, network_shp, RID_field)
    arcpy.SelectLayerByAttribute_management("width_second_lyr", "NEW_SELECTION",
                                             os.path.basename(network_shp) + "." + main_field + " = 0")
    try:


        # Join the main channels points to the secondary channels ones
        join_channels = arcpy.CreateScratchName("join", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
        arcpy.SpatialJoin_analysis("width_second_lyr", "width_main_lyr", join_channels, match_option="CLOSEST")
        gc.AddToGarbageBin(join_channels)

        #  The Spatial join creates weird field names. The best way to find back the name of a field after the spatial join is to use the field position in the table
        main_widthid_field = arcpy.ListFields(join_channels)[len(arcpy.ListFields(join_channels)) - len(arcpy.ListFields("width_main_lyr")) + [f.name for f in arcpy.ListFields("width_main_lyr")].index(os.path.basename(widthdata)+"."+widthid)].name
        join_table = arcpy.da.TableToNumPyArray(join_channels, [width_RID_field, main_widthid_field, width_field, main_distance_field])
        # compute values for the same main channel points and same secondary channel -> average
        means_table = np.unique(join_table[[width_RID_field, main_widthid_field]])
        means = []
        for i in means_table:
            tmp = join_table[np.where(join_table[[width_RID_field, main_widthid_field]] == i)]
            means.append(np.mean(tmp[width_field]))
        means_table = rfn.merge_arrays([means_table, np.array(means, dtype=[("width_avg", "f4")])], flatten=True)
        # merge the computed averages for the secondary channels with the values in the main channels
        main_table = arcpy.da.TableToNumPyArray("width_main_lyr", [os.path.basename(widthdata) + "." +widthid, os.path.basename(widthdata) + "." +width_field])
        main_table.dtype.names = [widthid, width_field]
        means_table = means_table[[main_widthid_field, "width_avg"]]
        means_table.dtype.names = [widthid, width_field]

        # record the minimum and maximum distance (on the main channel), for each secondary channel, to filter out unmatched points
        main_distance_field = arcpy.ListFields(join_channels)[
            len(arcpy.ListFields(join_channels)) - len(arcpy.ListFields("width_main_lyr")) + [f.name for f in
                                                                                              arcpy.ListFields(
                                                                                                  "width_main_lyr")].index(
                os.path.basename(widthdata) + "." + width_distance)].name
        min_max_table = np.unique(join_table[[width_RID_field]])
        min_max = {}
        for i in min_max_table:
            tmp = join_table[np.where(join_table[[width_RID_field]] == i)]
            min_max[i[width_RID_field]] = (np.min(tmp[main_distance_field]), np.max(tmp[main_distance_field]))

        print(main_table.dtype.fields)
        print(means_table.dtype.fields)
        merge_table = np.concatenate((main_table, means_table))
        sums_table = np.unique(merge_table[[widthid]])
        sums = []
        for i in sums_table:
            tmp = merge_table[np.where(merge_table[[widthid]] == i)]
            sums.append(np.sum(tmp[width_field]))
        sum_table = rfn.merge_arrays([sums_table, np.array(sums, dtype=[("width", "f8")])], flatten=True)

        # export
        arcpy.da.NumPyArrayToTable(sum_table, widthoutput)

        ### Test with Dissolve. Doesn't work because it creates Multipoints. Better to work with just the tables instead as numpy arrays (although it could have been simpler with Panda).
        # Group (Dissolve) the values from the same secondary channel and the same main channel points -> average
        # dissolve_avg = arcpy.CreateScratchName("dissolve", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
        # arcpy.Dissolve_management(join_channels, dissolve_avg, [width_RID_field, main_widthid_field], [[width_field, "MEAN"]])
        # gc.AddToGarbageBin(dissolve_avg)
        # # Group (Dissolve) the computed values for the same main channel points -> sum
        # print([f.name for f in arcpy.ListFields(dissolve_avg)])
        # print([f.name for f in arcpy.ListFields("width_main_lyr")])
        # #  First, the previous result (dissolve_avg) must be merge with the main channels points
        # #  Field mapping:
        # #   - in the dissolve_avg, the point ID of the main reach from the spatial join (main_widthid_field), with the point ID of the main reach
        # fldMap_id = arcpy.FieldMap()
        # fldMap_id.addInputField(dissolve_avg, main_widthid_field)
        # fldMap_id.addInputField("width_main_lyr", os.path.basename(widthdata) + "." + widthid)
        # fieldName = fldMap_id.outputField
        # fieldName.name = widthid
        # fldMap_id.outputField = fieldName
        # #   - in the dissolve_avg, the computed width average (last field), with the width average of the main reach
        # mean_field = arcpy.ListFields(dissolve_avg)[-1].name
        # fldMap_width = arcpy.FieldMap()
        # fldMap_width.addInputField("width_main_lyr", os.path.basename(widthdata) + "." + width_field)
        # fldMap_width.addInputField(dissolve_avg, mean_field)
        # fieldName2 = fldMap_width.outputField
        # fieldName2.name = width_field
        # fldMap_width.outputField = fieldName2
        #
        # fieldMappings = arcpy.FieldMappings()
        # fieldMappings.addFieldMap(fldMap_id)
        # fieldMappings.addFieldMap(fldMap_width)
        # merge = arcpy.CreateScratchName("merge", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
        # arcpy.Merge_management(["width_main_lyr", dissolve_avg], merge, fieldMappings)
        # gc.AddToGarbageBin(merge)
        # dissolve_sum = arcpy.CreateScratchName("dissolve", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
        # arcpy.Dissolve_management(merge, widthoutput, [widthid],
        #                           [[width_field], "SUM"])
        # gc.AddToGarbageBin(dissolve_avg)
    finally:
        gc.CleanAllTempFiles()

