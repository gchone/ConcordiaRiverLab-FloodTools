# -*- coding: utf-8 -*-

# ******************************************************************************
# Auteur: François Larouche-Tremblay, Ing, M Sc
# Date: 20/11/2020
# Description: Fonction qui applique un algorithme de découpage des
# tronçons sur les données raster et découpe la ligne centrale.
# ******************************************************************************

# Version 1.0 - 15/01/2019
# Première version de l'algorithme implémentée avec des points le long du "stream raster"

# Version 2.0 - 23/02/2020
# Jonction des algorithmes TransectsEquidistants et DecouperTronconsParker dans un même outil
# Implémentation avec numpy pour accélérer le traitement et stream raster remplacé par des transects le long
# d'un réseau vectoriel; transects en forme de pointe pour mieux représenté les confluences.

# Version 3.0 - 20/11/2020
# Correction de bogues et optimisation: départ à la position 0.0001 au lieu de 0 afin d'éviter que le premier
# transect ne sorte du polygone de surface de l'eau.

import arcpy
import numpy as np
from os.path import normpath, join, basename
from arcpy import env, CreateScratchName
from arcpy.lr import LocateFeaturesAlongRoutes, MakeRouteEventLayer
from arcpy.management import AddField, CalculateField, SelectLayerByLocation, Delete, MakeFeatureLayer, \
    DeleteIdentical, FeatureVerticesToPoints, JoinField, AlterField, SplitLineAtPoint, CopyFeatures, \
    SelectLayerByAttribute, MultipartToSinglepart, DeleteRows, DeleteField, Merge, GetRasterProperties, PolygonToLine, \
    Dissolve, FeatureToLine, CreateTable, PointsToLine
from arcpy.analysis import Intersect, Buffer, Statistics, Erase, Near, CreateThiessenPolygons, SpatialJoin
from arcpy.cartography import SmoothLine
from arcpy.ddd import StackProfile
# from arcpy.edit import Snap
from arcpy.da import NumPyArrayToTable, TableToNumPyArray, FeatureClassToNumPyArray
from arcpy.conversion import RasterToPoint
from arcpy.sa import Raster, ExtractByMask
# "Unresolved references" manuellement ignorées dans l'IDE


def addfieldtoarray(inarr, *fields):
    # **************************************************************************
    # DÉFINITION :
    # Ajoute un ou des champs à une "structured array"
    # ENTRÉES :
    # inarr: structured array
    # fields: name ou (name, dtype)

    # SORTIE :
    # outarr: structured array avec des champs supplémentaires
    # **************************************************************************
    old_fields = inarr.dtype.descr
    if len(old_fields) > len(inarr.dtype.fields):  # Si la matrice est une "view", elle a un champ bidon de plus?
        old_fields = old_fields[:-1]

    for field in fields:
        if isinstance(field, str):
            old_fields.append((field, np.float32))
        elif isinstance(field, tuple):
            old_fields.append(field)

    new_dtype = np.dtype(old_fields)
    outarr = np.empty(inarr.shape, dtype=new_dtype)
    for name in inarr.dtype.names:
        outarr[name] = inarr[name]

    return outarr


class NameGen(object):
    def __init__(self, prefix, directory):
        self.filecount = 0
        self.prefix = prefix
        self.directory = directory
        self.tablelist = []
        # ajouter self.digits au besoin

    def createtablename(self, name=None):
        if name:
            tablename = "{0}{1:02d}_{2}".format(self.prefix, self.filecount, name)
        else:
            tablename = "{0}{1:02d}".format(self.prefix, self.filecount)

        tabledir = normpath(join(self.directory, tablename))
        self.filecount += 1
        self.tablelist.append(tabledir)

        return tabledir

    def wipetables(self):
        for table in self.tablelist:
            Delete(table)
        # ajouter la possibilité d'exclure des tables

        return


class Dataset(object):
    # **************************************************************************
    # DÉFINITION :
    # Chemin d'accès vers un jeu de données ArcGIS. (directory : string)
    # (data_type : String) Peut avoir un identifiant de catégorie. (memslot : int)
    # **************************************************************************

    def __init__(self, directory, data_type, memslot=0):
        self.directory = directory
        self.datatype = data_type
        self.memslot = memslot


class ScratchIndex(object):
    # **************************************************************************
    # DÉFINITION :
    # Index pour la gestion et la suppression des couches de
    # données temporaires. Tous les types de données ArcGIS sont pris en charge
    # (Exemple: "FeatureClass", "RasterDataset"), en plus du type maison "Table".
    # **************************************************************************
    def __init__(self, dirlist=None):
        if dirlist is None:
            dirlist = []

        self.dirlist = dirlist
        self.filecount = len(self.dirlist)
        self.tablecount = 0
        for dataset in dirlist:
            if dataset.datatype == "Table":
                self.tablecount += 1

    def scratchname(self, prefix, data_type, workspace="memory", memslot=99):
        # **************************************************************************
        # DÉFINITION :
        # Permet de générer des noms de données temporaires avec
        # un préfix (prefix : String) et un numéro unique, ayant le bon format
        # selon le type de données. (data_type : String) Si le workspace n'est
        # pas spécifié, la donnée sera enregistrée en mémoire. Le jeu de donnée
        # peut être associé à une catégorie.
        # **************************************************************************

        if data_type == "Table":
            workspace = env.scratchWorkspace  # Les tables ne peuvent être créées en mémoire
            tablename = "t{0}{1:02d}".format(prefix, self.tablecount)
            name = normpath(join(workspace, tablename))
            self.tablecount += 1
        else:
            name = CreateScratchName(prefix, data_type=data_type, workspace=workspace)

        self.dirlist.append(Dataset(name, data_type, memslot))
        self.filecount = len(self.dirlist)

        return name

    def addtoscratch(self, directory, data_type, memslot=0):
        # **************************************************************************
        # DÉFINITION :
        # Permet d'ajouter un jeu de données déjà existant
        # (directory : string) (data_type : String) à la liste des couches
        # temporaires et de l'associer à une catégorie. (memslot : int)
        # **************************************************************************

        self.dirlist.append(Dataset(directory, data_type, memslot))
        self.filecount = len(self.dirlist)
        if data_type == "Table":
            self.tablecount += 1

        return

    def wipeindex(self, memslot=None):
        # **************************************************************************
        # DÉFINITION :
        # Permet d'effacer tous les jeux de données temporaires
        # ou seulement ceux de certaines catégories. (memslot : int)
        # **************************************************************************

        if memslot is None:
            garbagebin = [ds.directory for ds in self.dirlist]
            self.dirlist = []
            self.filecount = len(self.dirlist)
            self.tablecount = 0
        else:
            newdirlist = [ds for ds in self.dirlist if ds.memslot != memslot]
            garbagebin = [ds.directory for ds in self.dirlist if ds.memslot == memslot]
            self.dirlist = newdirlist
            self.filecount = len(self.dirlist)
            self.tablecount = 0
            for dataset in self.dirlist:
                if dataset.datatype == "Table":
                    self.tablecount += 1

        for directory in garbagebin:
            Delete(directory)


def deleteuselessfields(feature, keepers, mapping="FC"):
    # **************************************************************************
    # DÉFINITION :
    # Supprime tous les champs de la table qui ne sont pas listés dans keepers.

    # ENTRÉES :
    # feature = chemin d'accès vers la table ou la feature class, ou objet FieldMappings
    # keepers = Liste de noms de champs à conserver
    # mapping = STRING, indique si l'objet à modifier est la table d'attribut
    # de la feature class (FC) ou un FieldMappings (FMS)

    # SORTIE :
    # Les champs inutiles de la feature originale sont supprimés.
    # **************************************************************************
    fieldnames = [kp.upper() for kp in keepers]
    if mapping == "FMS":
        for field in feature.fields:
            fname = field.name
            if fname.upper() not in fieldnames:  # On conserve seulement les champs désirés
                feature.removeFieldMap(feature.findFieldMapIndex(fname))

        return feature

    for field in arcpy.ListFields(feature):
        fname = field.name
        if fname.upper() not in fieldnames:
            DeleteField(feature, fname)
    return


def getfieldproperty(feature, fieldname, prop, default=None):
    # **************************************************************************
    # DÉFINITION :
    # Effectue une requête pour extraire les propriétés et les champs demandés.

    # ENTRÉES :
    # feature = chemin d'accès vers la table ou la feature class
    # fieldname = nom de champ
    # prop = STRING, propriété à extraire
    # field.property : type, editable, required, scale, precision
    # SORTIE :
    # Les propriétés demandées
    # **************************************************************************
    for field in arcpy.ListFields(feature):
        fname = field.name
        if fname == fieldname:
            fieldattr = getattr(field, prop)
            if prop == "type":
                fieldattr = fieldattr.upper()

            return fieldattr

    return default


def pointsdextremites(streamnetwork, banklines, cellsize, endpoints):
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

    tempindex = ScratchIndex()  # Régistre des couches de données temporaires

    # Création d'un ensemble de points aux extrémités aval des tronçons
    confpts = tempindex.scratchname("ptex", "FeatureClass", workspace=env.scratchWorkspace)
    FeatureVerticesToPoints(streamnetwork, confpts, "END")
    DeleteIdentical(confpts, ["Shape"])  # Suppression des doublons

    # Suppression des points aval qui ne sont pas des confluences
    dangpts = tempindex.scratchname("mptex", "FeatureClass")
    FeatureVerticesToPoints(streamnetwork, dangpts, "DANGLE")
    MakeFeatureLayer(confpts, "confpts_lyr")
    SelectLayerByLocation("confpts_lyr", "INTERSECT", dangpts, "", "NEW_SELECTION")
    DeleteRows("confpts_lyr")
    SelectLayerByAttribute("confpts_lyr", "CLEAR_SELECTION")

    # Calcul de la distance des points de confluence avec la berge la plus proche
    Near(confpts, banklines, None, "NO_LOCATION", "NO_ANGLE", "PLANAR")
    AddField(confpts, "Buff_dist", "FLOAT")
    CalculateField(confpts, "Buff_dist", "!NEAR_DIST! + {0}".format(2 * cellsize), "PYTHON3")  # Résolution du MNT

    # Création d'un ensemble de points situés immédiatement en amont ou en aval des points de confluence
    confbuff = tempindex.scratchname("mptex", "FeatureClass")
    Buffer(confpts, confbuff, "Buff_dist", "FULL", "ROUND", "NONE", "", "PLANAR")

    buffend = tempindex.scratchname("mptex", "FeatureClass")
    Intersect([confbuff, streamnetwork], buffend, "ALL", "", "POINT")
    MultipartToSinglepart(buffend, endpoints)  # avant on mergeait avec le dangpts, maintenant non

    # Suppression des couches de données temporaires
    tempindex.wipeindex()

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
    tempindex = ScratchIndex()  # Régistre des couches de données temporaires

    idln = FeatureClassToNumPyArray(streamnetwork, [idfield, "SHAPE@LENGTH"], null_value=-9999)
    forkid = idln[idfield]
    length = idln["SHAPE@LENGTH"]
    strt = np.zeros(length.shape)
    stop = np.copy(length)
    tips = np.tile(np.array([1, 1, 1, 0]), [length.shape[0], 1])

    # Afin d'exclure les zones de confluence, les points de mesure sont générés entre les points d'extrémités (inclus)
    # Si les points d'extrémités ne sont pas spécifiés, les points de mesure sont générés sur toute la longueur.
    if endpoints is not None:
        endevnt = tempindex.scratchname("ptme", "Table", workspace=sws)
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
    temptabl = tempindex.scratchname("ptme", "Table", workspace=sws)
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

        if (so - sa) < (3 * spacing):
            arcpy.AddMessage("La branche {0} est trop courte, elle ne peut être traitée.".format(fkid, 4 * spacing))
            continue

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
    s1evnt = tempindex.scratchname("ptme", "Table", workspace=sws)
    NumPyArrayToTable(s1arr, s1evnt)
    eventtype = "{0} Point {1}".format(idfield, distfield)
    MakeRouteEventLayer(streamnetwork, idfield, s1evnt, eventtype, "s1evnt_lyr", None)
    CopyFeatures("s1evnt_lyr", datapoints)  # Enregistrement des points de repère de distance et du type de chaque CS

    # Suppression des couches de données temporaires
    tempindex.wipeindex()

    return


def transectsauxpointsdemesure(streamnetwork, idfield, smoothtol, cspoints, csfield, distfield, typefield,  maxwidth,
                               riverbanks, transects):
    # **************************************************************************
    # DÉFINITION :
    # Génère des transects rectilignes avec un espacement régulier sur toutes les
    # branches du réseau en excluant les confluences.

    # ENTRÉES :
    # streamnetwork = STRING, chemin d'accès vers le réseau de référencement linéaire
    # idfield = STRING, nom du champ contenant les identifiants de tronçons
    # smoothtol = FLOAT, tolérance pour le lissage du réseau
    #                    (le lissage améliore l'orientation des transects)
    # cspoints = STRING, chemin d'accès vers les points de positionnement des
    #                    transects. Les points doivent contenir un champ qui
    #                    indique le type des transects, soit:
    #                    CSTYPE : Normal = 1, Confluence = 0, Start = 2, Stop = 3
    # csfield = STRING, nom du champ qui contiendra un identifiant unique de point (Exemple: "CSid")
    # distfield = STRING, nom du champ qui contiendra la distance par rapport à l'amont (Exemple: "Distance_m")
    # typefield = STRING, nom du champ qui contient le type de transect
    # spacing = FLOAT, espacement entre les points de mesure
    # maxwidth = FLOAT, largeur maximale des transects
    # riverbanks = STRING, chemin d'accès vers les lignes de berge des cours d'eau; les transects
    #                    seront contenus à l'intérieur des berges
    # transects = STRING, emplacement où seront enregistrés les transects

    # offset=0, possibilité d'ajouter un offset pour tester la sensibilité du placement des sections

    # SORTIE :
    # transects = STRING, les transects sont enregistrés sous forme de lignes
    # **************************************************************************
    mflag = env.outputMFlag
    sws = env.scratchWorkspace
    tempindex = ScratchIndex()  # Régistre des couches de données temporaires

    env.outputMFlag = "Enabled"  # Pour que le réseau simplifié conserve ses coordonnées m
    eventtype = "{0} Point {1}".format(idfield, distfield)

    MakeFeatureLayer(cspoints, "cspoints_lyr")
    SelectLayerByAttribute("cspoints_lyr", "NEW_SELECTION", '"{0}" >= 1'.format(typefield), "")
    if smoothtol > 0:
        network = tempindex.scratchname("gtrpt", "FeatureClass", workspace=sws)
        tol = "{0:3.1f} Meters".format(smoothtol)
        SmoothLine(streamnetwork, network, "PAEK", tol, "FIXED_CLOSED_ENDPOINT", "RESOLVE_ERRORS", riverbanks)

        smtevnt = tempindex.scratchname("trpt", "Table", workspace=sws)
        eventtype = "SMPRouteid Point SMPMeasure"
        radius = "{0} Meters".format(smoothtol/2)
        LocateFeaturesAlongRoutes("cspoints_lyr", network, idfield, radius, smtevnt, eventtype, "ALL", "NO_DISTANCE")
        csarr = TableToNumPyArray(smtevnt, [csfield, "SMPRouteid", "SMPMeasure"], null_value=-9999)
    else:
        network = streamnetwork  # Permet de générer les évènements sur le réseau non simplifié
        csarr = TableToNumPyArray("cspoints_lyr", [csfield, idfield, distfield], null_value=-9999)

    SelectLayerByAttribute("cspoints_lyr", "CLEAR_SELECTION")
    csarr = np.sort(csarr, order=csfield)  # Au cas où l'ordre des points aurait été mélangé

    env.outputMFlag = mflag  # Retour à l'état initial

    # On ajoute le champ et les valeurs de offset pour générer les évènements de chaque côté du réseau
    ofstfield = "Offset"
    transarr = addfieldtoarray(np.repeat(csarr, 2), (ofstfield, '<f8'))  # Deux points pour chaque transects
    transarr[ofstfield] = np.tile([maxwidth / 2, -maxwidth / 2], csarr.shape[0])

    # Création des transects en reliant les points générés de part et d'autre du réseau de cours d'eau
    transevnt = tempindex.scratchname("trpt", "Table", workspace=sws)
    NumPyArrayToTable(transarr, transevnt)
    MakeRouteEventLayer(network, idfield, transevnt, eventtype, "transevnt_lyr", offset_field=ofstfield)

    rawtrans = tempindex.scratchname("trpt", "FeatureClass", workspace=sws)
    PointsToLine("transevnt_lyr", rawtrans, csfield, "", "NO_CLOSE")  # Memory leak?? Polyline()

    transends = tempindex.scratchname("trpt", "FeatureClass", workspace=sws)
    Intersect([rawtrans, riverbanks], transends, "ONLY_FID", "", "POINT")

    # Découpage des transects brutes en fonction des lignes de berges
    SplitLineAtPoint(rawtrans, transends, transects, "0.05 Meters")
    deleteuselessfields(transects, ["SHAPE_LENGTH", "OBJECTID", "SHAPE"], mapping="FC")

    # Suppression des couches de données temporaires
    tempindex.wipeindex()

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

    tempindex = ScratchIndex()  # Régistre des couches de données temporaires

    MakeFeatureLayer(cspoints, "cspts_lyr")
    SelectLayerByAttribute("cspts_lyr", "NEW_SELECTION", '"{0}" >= 2'.format(typefield))

    thiepoly = tempindex.scratchname("mtrco", "FeatureClass")
    CreateThiessenPolygons("cspts_lyr", thiepoly, "ALL")

    disspoly = tempindex.scratchname("mtrco", "FeatureClass")
    Dissolve(thiepoly, disspoly, "CSType", "", "SINGLE_PART", "DISSOLVE_LINES")

    conftrans = tempindex.scratchname("trco", "FeatureClass", workspace=sws)
    FeatureToLine([disspoly], conftrans, "0.001 Meters", "NO_ATTRIBUTES")

    transends = tempindex.scratchname("trco", "FeatureClass", workspace=sws)
    Intersect([conftrans, riverbanks], transends, "ONLY_FID", "", "POINT")

    # Découpage des transects brutes en fonction des lignes de berges
    SplitLineAtPoint(conftrans, transends, transects, "0.05 Meters")
    deleteuselessfields(transects, ["SHAPE_LENGTH", "OBJECTID", "SHAPE"], mapping="FC")

    # Suppression des couches de données temporaires
    tempindex.wipeindex()

    # Sélection des transects et suppression des lignes situés à l'extérieur des lignes de berge
    MakeFeatureLayer(transects, "splitrans_lyr")
    SelectLayerByLocation("splitrans_lyr", "INTERSECT", cspoints, "", "NEW_SELECTION", "INVERT")
    DeleteRows("splitrans_lyr")
    SelectLayerByAttribute("splitrans_lyr", "CLEAR_SELECTION")

    return


def elevationdestransects(transects, mnt, units, elevstat, elevfield):
    # **************************************************************************
    # DÉFINITION :
    # Prélève la statistique d'élévation calculée le long de chacun de chaque
    # transect (médiane, moyenne ou minimale)

    # ENTRÉES :
    # transects = STRING, chemin d'accès vers les transects (polyline)
    # cspoints = STRING, chemin d'accès vers les points de positionnement des
    #                    transects.
    # mnt = STRING, chemin d'accès vers le MNT corrigé qui a servi
    #               pour le pré-traitement
    # units = STRING, unités du MNT (M, CM)
    # elevstat = STRING, choix de la statistique d'élévation (MEDIAN, MEAN, MOY)
    # elevfield = STRING, nom du champ qui contiendra la statistique d'élévation

    # SORTIE :
    # La table d'attribut des transects et des points de positionnement est
    # modifiée pour y ajouter un champ contenant la statistique d'élévation
    # **************************************************************************
    # mflag = env.outputMFlag
    # env.outputMFlag = "Disabled"
    sws = env.scratchWorkspace

    tempindex = ScratchIndex()  # Régistre des couches de données temporaires
    table1 = tempindex.scratchname("eltr", "Table", workspace=sws)
    # ESSAYER AVEC INTERPOLATE SHAPE POUR PASSER PAR LES MESURES DU RASTER!!!
    # arcpy.3d.InterpolateShape(in_surface, in_feature_class, out_feature_class,
    # {sample_distance}, {z_factor}, {method}, {vertices_only}, {pyramid_level_resolution}, {preserve_features})

    temptrans = tempindex.scratchname("trpt", "FeatureClass", workspace=sws)
    CopyFeatures(transects, temptrans)

    cellsize = int(GetRasterProperties(mnt, "CELLSIZEY").getOutput(0))
    StackProfile(temptrans, mnt, table1)
    table2 = tempindex.scratchname("eltr", "Table", workspace=sws)
    if elevstat == "OPTIMAL":
        Statistics(table1, table2, [["FIRST_Z", "MIN"]], "LINE_ID")
        fname = "MEDIAN_FIRST_Z"
        table3 = tempindex.scratchname("eltr", "Table", workspace=sws)
        Statistics(table1, table3, [["FIRST_Z", "MEDIAN"]], "LINE_ID")
        JoinField(temptrans, "OBJECTID", table2, "LINE_ID", "MIN_FIRST_Z")
        JoinField(temptrans, "OBJECTID", table3, "LINE_ID", fname)
        MakeFeatureLayer(temptrans, "transects_lyr")
        SelectLayerByAttribute("transects_lyr", "NEW_SELECTION", '"SHAPE_LENGTH" <= {0}'.format(6 * cellsize))
        CalculateField("transects_lyr", fname, "!MIN_FIRST_Z!", "PYTHON3")
        SelectLayerByAttribute("transects_lyr", "CLEAR_SELECTION")
    else:
        Statistics(table1, table2, [["FIRST_Z", elevstat]], "LINE_ID")
        fname = "{0}_FIRST_Z".format(elevstat)
        JoinField(temptrans, "OBJECTID", table2, "LINE_ID", fname)

    fdict = {"MEAN": "moyenne", "MEDIAN": "médiane", "MIN": "minimale", "OPTIMAL": "optimale"}
    elevfield = "{0}_{1}".format(elevfield, elevstat)  # Nom du champ contenant l'élévation ajouté à la table
    falias = "Élévation {0} du transect (m)".format(fdict[elevstat])
    # Ajouté un arrondi!!
    AddField(temptrans, elevfield, "FLOAT", field_alias=falias)
    if units == "CM":  # L'élévation est convertie en mètre au besoin.
        CalculateField(temptrans, elevfield, "round(!{0}!/100, 2)".format(fname), "PYTHON3")
    else:
        CalculateField(temptrans, elevfield, "round(!{0}!, 2)".format(fname), "PYTHON3", '', "TEXT")
        # AlterField(transects, fname, nfname, falias)

    JoinField(transects, "OBJECTID", temptrans, "OBJECTID", elevfield)  # Seulement le champ nécessaire

    # env.outputMFlag = mflag  # L'environnement est remis à son état initial

    # Suppression des couches de données temporaires
    tempindex.wipeindex()

    return


def transectsverspoints(transects, tol, datapoints):
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
    tempindex = ScratchIndex()

    oldpts = tempindex.scratchname("trpt", "FeatureClass", workspace=env.scratchWorkspace)
    CopyFeatures(datapoints, oldpts)

    MakeFeatureLayer(oldpts, "datapts_lyr")
    SelectLayerByLocation("datapts_lyr", "INTERSECT", transects, "0.1 Meters", "NEW_SELECTION")
    fms.addTable("datapts_lyr")

    tol = "{0} Meters".format(tol)
    SpatialJoin("datapts_lyr", transects, datapoints, "JOIN_ONE_TO_ONE", "KEEP_ALL", fms, "WITHIN_A_DISTANCE", tol, None)

    deleteuselessfields(datapoints, fieldnames, mapping="FC")

    tempindex.wipeindex()

    return


def elevation2destransects(transects, riverbed, mnt, units, elevstat, elevfield):
    # **************************************************************************
    # DÉFINITION :
    # Prélève la statistique d'élévation calculée le long de chacun de chaque
    # transect (médiane, moyenne ou minimale)

    # ENTRÉES :
    # transects = STRING, chemin d'accès vers les transects (polyline)
    # cspoints = STRING, chemin d'accès vers les points de positionnement des
    #                    transects.
    # mnt = STRING, chemin d'accès vers le MNT corrigé qui a servi
    #               pour le pré-traitement
    # units = STRING, unités du MNT (M, CM)
    # elevstat = STRING, choix de la statistique d'élévation (MEDIAN, MEAN, MOY)

    # SORTIE :
    # La table d'attribut des transects et des points de positionnement est
    # modifiée pour y ajouter un champ contenant la statistique d'élévation
    # **************************************************************************
    sws = env.scratchWorkspace

    tempindex = ScratchIndex()  # Régistre des couches de données temporaires
    demras = Raster(mnt)
    cellsize = demras.meanCellHeight

    env.cellSize = demras
    env.snapRaster = demras
    env.extent = demras

    fieldnames = [f.name for f in arcpy.ListFields(transects)]

    tempbed = tempindex.scratchname("reltr", "RasterDataset", workspace=sws)
    bedras = ExtractByMask(mnt, riverbed)
    bedras.save(tempbed)

    bedelevpts = tempindex.scratchname("eltr", "FeatureClass", workspace=sws)
    RasterToPoint(tempbed, bedelevpts, "VALUE")

    temptrans = tempindex.scratchname("eltr", "FeatureClass", workspace=sws)
    CopyFeatures(transects, temptrans)

    fms = arcpy.FieldMappings()  # Table d'attribut suite à l'ajout des extrémités des pré-découpages/confluences
    fms.addTable(temptrans)
    fms.addTable(bedelevpts)
    fieldid = fms.findFieldMapIndex("grid_code")
    fmapmed = fms.getFieldMap(fieldid)
    fmapmin = fms.getFieldMap(fieldid)

    fmapmed.mergeRule = "Median"
    field = fmapmed.outputField
    field.name = "ELEV_MEDIAN"
    field.aliasName = "Élévation médiane du transect (m)"
    fmapmed.outputField = field
    fms.replaceFieldMap(fieldid, fmapmed)

    fmapmin.mergeRule = "Min"
    field = fmapmin.outputField
    field.name = "ELEV_MIN"
    field.aliasName = "Élévation minimale du transect (m)"
    fmapmin.outputField = field
    fms.addFieldMap(fmapmin)

    tol = "{0} Meters".format((2**0.5) * cellsize)
    SpatialJoin(temptrans, bedelevpts, transects, "JOIN_ONE_TO_ONE", "KEEP_ALL", fms, "WITHIN_A_DISTANCE", tol, None)

    fdict = {"MEDIAN": "médiane", "MIN": "minimale", "OPTIMAL": "optimale"}
    elevfield = "{0}_{1}".format(elevfield, elevstat)  # Nom du champ contenant l'élévation ajouté à la table
    falias = "Élévation {0} du transect (m)".format(fdict[elevstat])

    AddField(transects, elevfield, "FLOAT", field_alias=falias)
    if units == "CM":  # L'élévation est convertie en mètre au besoin.
        equation = "round(!{0}!/100, 2)"
    else:
        equation = "round(!{0}!, 2)"

    if elevstat == "OPTIMAL":
        MakeFeatureLayer(transects, "transects_lyr")
        SelectLayerByAttribute("transects_lyr", "NEW_SELECTION", '"SHAPE_LENGTH" <= {0}'.format(6 * cellsize))
        CalculateField("transects_lyr", elevfield, equation.format("ELEV_MIN"), "PYTHON3")
        SelectLayerByAttribute("transects_lyr", "SWITCH_SELECTION")
        CalculateField("transects_lyr", elevfield, equation.format("ELEV_MEDIAN"), "PYTHON3")
        SelectLayerByAttribute("transects_lyr", "CLEAR_SELECTION")
    else:
        CalculateField(transects, elevfield, equation.format("ELEV_" + elevstat), "PYTHON3")

    fieldnames.extend(["ELEV_MEDIAN", "ELEV_MIN", elevfield])
    deleteuselessfields(transects, fieldnames, mapping="FC")
    # Suppression des couches de données temporaires
    tempindex.wipeindex()

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
    # cellsize = int(GetRasterProperties(mnt, "CELLSIZEY").getOutput(0))
    mflag = env.outputMFlag
    sws = env.scratchWorkspace
    tempindex = ScratchIndex()

    env.outputMFlag = "Disabled"  # Pour que DeleteIdentical fonctionne aux confluences

    # Nettoyage des transects qui traversent deux chenaux ou plus
    overlaps = tempindex.scratchname("latr", "FeatureClass", workspace=sws)
    Intersect([transects, streamnetwork], overlaps, "ALL", "", "POINT")

    singols = tempindex.scratchname("latr", "FeatureClass", workspace=sws)
    MultipartToSinglepart(overlaps, singols)
    DeleteIdentical(singols, ["Shape"])  # Les transects aux confluences génèrent des doublons

    tabletemp = tempindex.scratchname("tlatr", "Table", workspace=sws)
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

    # Suppression des couches de données temporaires
    tempindex.wipeindex()

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
    tempindex = ScratchIndex()

    fname = "FID_{0}".format(basename(transects))
    MakeFeatureLayer(transects, "transects_lyr")
    for ii in range(5, nx, -1):
        overlaps = tempindex.scratchname("msucr", "FeatureClass")
        Intersect("transects_lyr", overlaps, "ONLY_FID", "", "POINT")

        tabletemp = tempindex.scratchname("sucr", "Table", workspace=sws)
        Statistics(overlaps, tabletemp, [[fname, "COUNT"]], fname)
        JoinField("transects_lyr", "OBJECTID", tabletemp, fname, "COUNT_{0}".format(fname))
        AlterField("transects_lyr", "COUNT_{0}".format(fname), "Overlap{0:02d}".format(ii))

        SelectLayerByAttribute("transects_lyr", "NEW_SELECTION", '"Overlap{0:02d}" >= {1}'.format(ii, ii), "")
        desc = arcpy.Describe("transects_lyr")
        if desc.FIDSet != "":
            DeleteRows("transects_lyr")

        SelectLayerByAttribute("transects_lyr", "CLEAR_SELECTION")
        DeleteField("transects_lyr", "COUNT_{0}".format(fname))  # On supprime le champ temporaire

    # Suppression des couches de données temporaires
    tempindex.wipeindex()

    return


def execute_largeurpartransect(streamnetwork, idfield, riverbed, ineffarea, maxwidth, spacing,
                               cellsize, mnt, units, elevstat, transects, cspoints, messages):
    # **************************************************************************
    # DÉFINITION :
    # Corps d'exécution (main) de l'outil de découpage des tronçons.

    # ENTRÉES :
    # minrchlen = int, (Ex. 96) Longueur minimale des tronçons finaux.
    # maxrchlen = int, (Ex. 1000, > 2X minrchlen) Longueur maximale des
    # tronçons finaux.
    # aggron = Bool, (Ex. True) Switch pour aggréger les sections de pente
    # similaire en pré-traitement
    # aggrthresh = float, (Ex. 0.4) Seuil de différence de pente pour
    # l'aggrégation des voisins.
    # forceslope = Bool, (Ex. True) Switch pour forcer une pente dans tous les
    # tronçons. (pas de pente nulle)
    # parkeron = Bool, (Ex. True) Switch pour activer l'algorithme de parker
    # cutzealot = Bool, (Ex. True) Switch pour couper (à intervalle fixe)
    # les tronçons qui sont encore trop longs après Parker

    # SORTIE :
    # **************************************************************************

    # **************************************************************************
    # Création des lignes des berges de cours d'eau

    sws = env.scratchWorkspace
    tempindex = ScratchIndex()

    if ineffarea and ineffarea != "#":
        effbed = tempindex.scratchname("mmexlt", "FeatureClass")
        Erase(riverbed, ineffarea, effbed)
        inpoly = effbed
    else:
        inpoly = riverbed

    csfield, distfield, typefield = "CSid", "Distance_m", "CSType"  # HARDCODED

    riverbanks = tempindex.scratchname("mexlt", "FeatureClass")
    PolygonToLine(inpoly, riverbanks, "IGNORE_NEIGHBORS")

    # Création d'un ensemble de points situés immédiatement en amont et en aval des points de confluence
    endcs = tempindex.scratchname("mexlt", "FeatureClass")
    pointsdextremites(streamnetwork, riverbanks, cellsize, endcs)

    # Création de l'ensemble de points où sera mesurée la largeur sur le réseau (entre les points d'extrémités)
    pointsdemesure(streamnetwork, idfield, csfield, distfield, typefield, spacing, cspoints, endcs)

    # Création des transects équidistants situés sur les branches de cours d'eau
    rawtrans = tempindex.scratchname("exlt", "FeatureClass", workspace=sws)
    smoothtol = 0  # 6 * cellsize
    transectsauxpointsdemesure(streamnetwork, idfield, smoothtol, cspoints, csfield, distfield,
                               typefield, maxwidth, riverbanks, rawtrans)

    # Création des transects en pointe situés aux confluences
    conftrans = tempindex.scratchname("exlt", "FeatureClass", workspace=sws)
    transectsauxconfluences(cspoints, typefield, riverbanks, conftrans)

    Merge([rawtrans, conftrans], transects)

    # Suppression des couches de données temporaires
    tempindex.wipeindex()

    widthfield = "Largeur_m"
    largeurdestransects(streamnetwork, transects, widthfield)

    nx = 2  # Nombre de croisements tolérés
    supprimercroisements(transects, nx)

    # Calcul et attribution de la statistique d'élévation à chacun des transects
    if mnt and mnt != "#":
        elevfield = "Elev_m"
        elevation2destransects(transects, riverbed, mnt, units, elevstat, elevfield)
        # elevationdestransects(transects, mnt, units, elevstat, elevfield)

    transectsverspoints(transects, 2 * cellsize, cspoints)

    return
