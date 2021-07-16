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
from DataManagementDEH import addfieldtoarray, deleteuselessfields, getfieldproperty

from tree.RiverNetwork import *
import ArcpyGarbageCollector as gc
from InterpolatePoints import *
import numpy.lib.recfunctions as rfn
from LocatePointsAlongRoutes import *

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



    # Création d'un ensemble de points aux extrémités aval des tronçons
    confpts = gc.CreateScratchName("pts", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
    FeatureVerticesToPoints(streamnetwork, confpts, "END")
    DeleteIdentical(confpts, ["Shape"])  # Suppression des doublons

    # Suppression des points aval qui ne sont pas des confluences
    dangpts = gc.CreateScratchName("mptex", data_type="FeatureClass", workspace="in_memory")
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
    confbuff = gc.CreateScratchName("mptex", data_type="FeatureClass", workspace="in_memory")
    Buffer(confpts, confbuff, "Buff_dist", "FULL", "ROUND", "NONE", "", "PLANAR")
    buffend = gc.CreateScratchName("mptex", data_type="FeatureClass", workspace="in_memory")
    Intersect([confbuff, streamnetwork], buffend, "ALL", "", "POINT")
    MultipartToSinglepart(buffend, endpoints)

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


    idln = FeatureClassToNumPyArray(streamnetwork, [idfield, "SHAPE@LENGTH"], null_value=-9999)
    forkid = idln[idfield]
    length = idln["SHAPE@LENGTH"]
    strt = np.zeros(length.shape)
    stop = np.copy(length)
    tips = np.tile(np.array([1, 1, 1, 0]), [length.shape[0], 1])

    # Afin d'exclure les zones de confluence, les points sont générés entre les points d'extrémités (inclus)
    # Si les points d'extrémités ne sont pas spécifiés, les points de mesure sont générés sur toute la longueur.
    if endpoints is not None:
        endevnt = gc.CreateScratchName("table", data_type="ArcInfoTable",
                                                  workspace=arcpy.env.scratchWorkspace)
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
    temptabl = gc.CreateScratchName("table", data_type="ArcInfoTable",
                                      workspace=arcpy.env.scratchWorkspace)
    CreateTable(sws, basename(temptabl))  # Champ OBJECTID créé avec la table

    fieldnames = [csfield, distfield, idfield, typefield]
    for field, dtype in zip(fieldnames, ["LONG", "FLOAT", idft, "LONG"]):
        AddField(temptabl, field, dtype)

    s1arr = TableToNumPyArray(temptabl, fieldnames, null_value=-9999)
    arrlist = []
    trows = 0
    dt1 = s1arr.dtype
    for sa, so, tip, ln, fkid in zip(strt, stop, tips, length, forkid):
        #arcpy.AddMessage("La branche {0} commence à {1}, finit à {2}, a une longueur de {3}.".format(fkid, sa, so, ln))

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
    s1evnt = gc.CreateScratchName("table", data_type="ArcInfoTable",
                                       workspace=arcpy.env.scratchWorkspace)
    NumPyArrayToTable(s1arr, s1evnt)

    eventtype = "{0} Point {1}".format(idfield, distfield)
    MakeRouteEventLayer(streamnetwork, idfield, s1evnt, eventtype, "s1evnt_lyr", None)
    CopyFeatures("s1evnt_lyr", datapoints)  # Enregistre les points de repère de distance et le type de chaque CS



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
    transevnt = gc.CreateScratchName("table", data_type="ArcInfoTable",
                                       workspace=arcpy.env.scratchWorkspace)
    NumPyArrayToTable(transarr, transevnt)


    eventtype = "{0} Point {1}".format(idfield, distfield)
    MakeRouteEventLayer(streamnetwork, idfield, transevnt, eventtype, "transevnt_lyr", offset_field=ofstfield)

    rawtrans = gc.CreateScratchName("trpt", data_type="FeatureClass",
                                        workspace=arcpy.env.scratchWorkspace)
    PointsToLine("transevnt_lyr", rawtrans, csfield, "", "NO_CLOSE")

    transends = gc.CreateScratchName("trpt", data_type="FeatureClass",
                                       workspace=arcpy.env.scratchWorkspace)
    Intersect([rawtrans, riverbanks], transends, "ONLY_FID", "", "POINT")

    # Découpage des transects brutes en fonction des lignes de berges
    SplitLineAtPoint(rawtrans, transends, transects, "0.05 Meters")
    deleteuselessfields(transects, ["SHAPE_LENGTH", "OBJECTID", "SHAPE"], mapping="FC")

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

    MakeFeatureLayer(cspoints, "cspts_lyr")
    SelectLayerByAttribute("cspts_lyr", "NEW_SELECTION", '"{0}" >= 2'.format(typefield))

    thiepoly = gc.CreateScratchName("mtrco", data_type="FeatureClass", workspace="in_memory")
    CreateThiessenPolygons("cspts_lyr", thiepoly, "ALL")

    disspoly = gc.CreateScratchName("mtrco", data_type="FeatureClass", workspace="in_memory")
    Dissolve(thiepoly, disspoly, "CSType", "", "SINGLE_PART", "DISSOLVE_LINES")

    conftrans = gc.CreateScratchName("trco", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
    FeatureToLine([disspoly], conftrans, "0.001 Meters", "NO_ATTRIBUTES")

    transends = gc.CreateScratchName("trco", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
    Intersect([conftrans, riverbanks], transends, "ONLY_FID", "", "POINT")

    # Découpage des transects brutes en fonction des lignes de berges
    SplitLineAtPoint(conftrans, transends, transects, "0.05 Meters")
    deleteuselessfields(transects, ["SHAPE_LENGTH", "OBJECTID", "SHAPE"], mapping="FC")


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

    fieldnames = [f.name for f in arcpy.ListFields(datapoints)] + [f.name for f in arcpy.ListFields(transects)]
    fms = arcpy.FieldMappings()  # Table d'attribut suite à l'ajout des extrémités des pré-découpages/confluences
    fms.addTable(transects)

    oldpts = gc.CreateScratchName("trpt", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
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

    env.outputMFlag = "Disabled"  # Pour que DeleteIdentical fonctionne aux confluences

    # Nettoyage des transects qui traversent deux chenaux ou plus
    overlaps = gc.CreateScratchName("latr", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
    Intersect([transects, streamnetwork], overlaps, "ALL", "", "POINT")

    singols = gc.CreateScratchName("latr", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
    MultipartToSinglepart(overlaps, singols)

    DeleteIdentical(singols, ["Shape"])  # Les transects aux confluences génèrent des doublons

    tabletemp = gc.CreateScratchName("table", data_type="ArcInfoTable", workspace=arcpy.env.scratchWorkspace)

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


    fname = "FID_{0}".format(basename(transects))
    MakeFeatureLayer(transects, "transects_lyr")
    for ii in range(5, nx, -1):
        overlaps = gc.CreateScratchName("msucr", data_type="FeatureClass", workspace="in_memory")
        Intersect("transects_lyr", overlaps, "ONLY_FID", "", "POINT")

        tabletemp = gc.CreateScratchName("table", data_type="ArcInfoTable", workspace="in_memory")
        Statistics(overlaps, tabletemp, [[fname, "COUNT"]], fname)
        gc.AddToGarbageBin(tabletemp)
        JoinField("transects_lyr", "OBJECTID", tabletemp, fname, "COUNT_{0}".format(fname))
        # AlterField("transects_lyr", "COUNT_{0}".format(fname), "Overlap{0:02d}".format(ii))

        # SelectLayerByAttribute("transects_lyr", "NEW_SELECTION", '"Overlap{0:02d}" >= {1}'.format(ii, ii), "")
        SelectLayerByAttribute("transects_lyr", "NEW_SELECTION", '"COUNT_{0}" >= {1}'.format(fname, ii), "")
        desc = arcpy.Describe("transects_lyr")
        if desc.FIDSet != "":
            DeleteRows("transects_lyr")

        SelectLayerByAttribute("transects_lyr", "CLEAR_SELECTION")
        DeleteField("transects_lyr", "COUNT_{0}".format(fname))  # On supprime le champ temporaire

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

    try:
        # Suppression des zones d'écoulement ineffectives
        if ineffarea and ineffarea != "#":
            effbed = gc.CreateScratchName("mmexlt", data_type="FeatureClass", workspace="in_memory")
            Erase(riverbed, ineffarea, effbed)
            inpoly = effbed
        else:
            inpoly = riverbed

        csfield, distfield, typefield = "CSid", "Distance_m", "CSType"  # HARDCODED

        # Création des lignes des berges de cours d'eau
        riverbanks = gc.CreateScratchName("mmexlt", data_type="FeatureClass", workspace="in_memory")
        PolygonToLine(inpoly, riverbanks, "IGNORE_NEIGHBORS")

        # Création d'un ensemble de points situés immédiatement en amont et en aval des points de confluence
        endcs = gc.CreateScratchName("mexlt", data_type="FeatureClass", workspace="in_memory")
        pointsdextremites(streamnetwork, riverbanks, endcs)

        # Création de l'ensemble de points où sera mesurée la largeur sur le réseau (entre les points d'extrémités)
        pointsdemesure(streamnetwork, idfield, csfield, distfield, typefield, spacing, cspoints, endcs)

        # Création des transects équidistants situés sur les branches de cours d'eau
        rawtrans = gc.CreateScratchName("exlt", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
        transectsauxpointsdemesure(streamnetwork, idfield, cspoints, csfield, distfield,
                                   typefield, maxwidth, riverbanks, rawtrans)
        gc.AddToGarbageBin(rawtrans)

        # Création des transects en pointe situés aux confluences
        conftrans = gc.CreateScratchName("exlt", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
        transectsauxconfluences(cspoints, typefield, riverbanks, conftrans)


        Merge([rawtrans, conftrans], transects)

        widthfield = "Largeur_m"  # HARDCODED
        largeurdestransects(streamnetwork, transects, widthfield)

        nx = 2  # Nombre de croisements tolérés
        supprimercroisements(transects, nx)

        transectsverspoints(transects, cspoints)

    finally:
        # Suppression des couches de données temporaires
        gc.CleanAllTempFiles()

    return

def execute_WidthPostProc(network_shp, RID_field, main_channel_field, network_main_only, RID_field_main, network_main_l_field, order_field, network_main_only_links, widthdata, widthid, width_RID_field, width_distance, width_field, datapoints, id_field_datapts, distance_field_datapts, rid_field_datapts, output_table, messages):
    try:
        messages.addMessage("Processing main channels")
        ### 1a - Project points in the main channel on the main_only network
        # Selection only the points on the main channels
        arcpy.MakeFeatureLayer_management(widthdata, "width_main_lyr")
        arcpy.AddJoin_management("width_main_lyr", width_RID_field, network_shp, RID_field)
        arcpy.SelectLayerByAttribute_management("width_main_lyr", "NEW_SELECTION",
                                                arcpy.Describe(network_shp).basename + "." + main_channel_field + " = 1")
        # Linear reference them on the network_main_only

        main_width_pts = gc.CreateScratchName("pts", data_type="ArcInfoTable", workspace="in_memory")
        arcpy.MakeFeatureLayer_management(network_shp, "network_lyr")
        arcpy.SelectLayerByAttribute_management("network_lyr", "NEW_SELECTION",
                                                main_channel_field + " = 1")
        splitted_to_unsplitted("network_lyr", RID_field, "width_main_lyr", widthid, width_RID_field, width_distance, width_field, network_main_only, RID_field_main, network_main_l_field, main_width_pts)

        ### 1b - Interpolate width data on datapoints
        interp_main_width_pts = gc.CreateScratchName("pts", data_type="ArcInfoTable", workspace="in_memory")
        execute_InterpolatePoints(main_width_pts, widthid, RID_field_main, width_distance, [width_field], datapoints, id_field_datapts, rid_field_datapts, distance_field_datapts, network_main_only, network_main_only_links, RID_field_main, order_field, interp_main_width_pts, extrapolation_value="CONFLUENCE")

        ### 2a - Project width point of secondary channels on the main_only network
        arcpy.MakeFeatureLayer_management(widthdata, "width_second_lyr")
        arcpy.AddJoin_management("width_second_lyr", width_RID_field, network_shp, RID_field)
        arcpy.SelectLayerByAttribute_management("width_second_lyr", "NEW_SELECTION",
                                                arcpy.Describe(network_shp).basename + "." + main_channel_field + " = 0")
        secondary_width_pts = gc.CreateScratchName("pts", data_type="ArcInfoTable", workspace="in_memory")
        # Points on secondary channels are projected on the closest main channel
        arcpy.LocateFeaturesAlongRoutes_lr("width_second_lyr", network_main_only, RID_field_main, 10000, secondary_width_pts,
                                          RID_field_main + " POINT MEAS", distance_field="NO_DISTANCE")

        ### 2b - Interpolate width data for every secondary channel (with 0 upstream and downstream of the secondary channel)
        ### 3 - Sum all width measurements
        secondary_channel_RID_field = [f.name for f in arcpy.ListFields(secondary_width_pts)][
            [f.name for f in arcpy.ListFields("width_main_lyr")].index(
                arcpy.Describe(widthdata).basename + "." + width_RID_field) + 1]
        secondary_width_pts_np = arcpy.da.TableToNumPyArray(secondary_width_pts, ["MEAS", width_field, secondary_channel_RID_field])
        secondary_RIDs = np.unique(secondary_width_pts_np[[secondary_channel_RID_field]])
        arcpy.MakeTableView_management(secondary_width_pts, "secondary_width_lyr")

        interp_main_width_pts_np = arcpy.da.TableToNumPyArray(interp_main_width_pts,
                                                            [id_field_datapts, "MEAS", RID_field_main, width_field])
        interp_main_width_pts_np = np.sort(interp_main_width_pts_np, order=id_field_datapts) # ordering to ensure match latter

        i=0
        for rid in secondary_RIDs:
            i+=1
            messages.addMessage("Processing secondary channels (" + str(i) + "/" + str(len(secondary_RIDs)) + ")")
            new_interp = gc.CreateScratchName("interp", data_type="ArcInfoTable", workspace=arcpy.env.scratchWorkspace)
            arcpy.SelectLayerByAttribute_management("secondary_width_lyr", "NEW_SELECTION",
                                                    secondary_channel_RID_field + " = " + str(rid[0]))

            execute_InterpolatePoints("secondary_width_lyr", widthid, RID_field_main, "MEAS", [width_field], datapoints,
                                      id_field_datapts, rid_field_datapts, distance_field_datapts, network_main_only,
                                      network_main_only_links, RID_field_main, order_field, new_interp, extrapolation_value=0)
            tmp_np = arcpy.da.TableToNumPyArray(new_interp, [id_field_datapts, width_field])
            tmp_np = np.sort(tmp_np, order=id_field_datapts)
            interp_main_width_pts_np[width_field] = interp_main_width_pts_np[width_field]+tmp_np[width_field]
            gc.CleanTempFile(new_interp)

        if arcpy.env.overwriteOutput and arcpy.Exists(output_table):
            arcpy.Delete_management(output_table)
        arcpy.da.NumPyArrayToTable(interp_main_width_pts_np, output_table)


    finally:
        # Suppression des couches de données temporaires
        gc.CleanAllTempFiles()


def splitted_to_unsplitted(splitted_net, splitted_RID_field, pts_lyr, pts_ID_field, pts_RID_field, pts_dist_field, width_field, unsplitted_net, unsplitted_RID_field, unslitted_l_field, outpts):
    # Find correspondance between a splitted and an unsplitted network

    # Find a RID match using a spatial join
    match_RID_table = gc.CreateScratchName("match", data_type="ArcInfoTable", workspace="in_memory")
    fms = arcpy.FieldMappings()
    # dans un premier temps j'ajoute le champ d'identification des iunités spatiales
    fmID = arcpy.FieldMap()
    fmID.addInputField(splitted_net, splitted_RID_field)
    type_name = fmID.outputField
    type_name.name = 'RID_A'
    fmID.outputField = type_name
    fms.addFieldMap(fmID)
    fmID_B = arcpy.FieldMap()
    fmID_B.addInputField(unsplitted_net, unsplitted_RID_field)
    type_name_B = fmID_B.outputField
    type_name_B.name = 'RID_B'
    fmID_B.outputField = type_name_B
    fms.addFieldMap(fmID_B)
    arcpy.SpatialJoin_analysis(splitted_net, unsplitted_net, match_RID_table, match_option="WITHIN", field_mapping=fms)

    # Then correct the distances, in points, using the distance of the "START" point of the splitted reach
    #  Find the start points
    start_pts = gc.CreateScratchName("pts", data_type="FeatureClass", workspace="in_memory")
    arcpy.FeatureVerticesToPoints_management(splitted_net, start_pts, "START")
    #  Join to have the unsplitted RID
    arcpy.MakeFeatureLayer_management(start_pts, "start_lyr")
    arcpy.AddJoin_management("start_lyr", splitted_RID_field, match_RID_table, "RID_A")
    #  Project start points on the right unsplitted reach
    splits_along = gc.CreateScratchName("split", data_type="ArcInfoTable", workspace="in_memory")
    execute_LocatePointsAlongRoutes("start_lyr", arcpy.Describe(match_RID_table).basename + ".RID_B", unsplitted_net, unsplitted_RID_field, splits_along, 1)
    #  Join the result to the data points
    arcpy.AddJoin_management(pts_lyr, pts_RID_field, splits_along, "RID_A")
    #  Join the river network to get the max possible length (needed to fix issues where the measured distance is slightly over the reach length
    arcpy.AddJoin_management(pts_lyr, arcpy.Describe(splits_along).basename+".RID_B", unsplitted_net, unsplitted_RID_field)

    #  Correct distances
    result_np = arcpy.da.TableToNumPyArray(pts_lyr, [arcpy.Describe(pts_lyr).basename+"."+pts_ID_field, arcpy.Describe(pts_lyr).basename+"."+width_field,
                                                     arcpy.Describe(pts_lyr).basename+"."+pts_dist_field, arcpy.Describe(splits_along).basename+".RID_B",
                                                     arcpy.Describe(splits_along).basename+".MEAS", arcpy.Describe(unsplitted_net).basename+"."+unslitted_l_field])
    result_np.dtype.names = [pts_ID_field, width_field, pts_dist_field, pts_RID_field, "MEAS", "Max_l"]
    result_np[pts_dist_field] = result_np[pts_dist_field] + result_np["MEAS"]
    result_np[pts_dist_field] = np.minimum(result_np[pts_dist_field], result_np["Max_l"])
    arcpy.da.NumPyArrayToTable(result_np[[pts_ID_field, width_field, pts_dist_field, pts_RID_field]], outpts)
