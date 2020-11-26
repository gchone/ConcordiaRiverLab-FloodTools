# coding: latin-1

# Fichier TreeManager.py
# v0.0.2 - 24/10/2017

### Contenu ###
# classe OurTreeManager : Classe de gestion générique d'un arbre avec OurTreeSegments

### Historique des versions ###
# v0.0.1 - 13/11/2018 - Création
# v0.1 - 22/05/2020 - Modification pour création d'arbre multiples
# v1.0 - Nov 2020 - Ajout de dossier en paramètre de données (kwargs): Crée un dictionnaire avec comme clé le nom de chaque raster du dossier
#  Ajout de X et Y pour les points


import tree.TreeManager as TreeManager
from tree.OurTreeSegment import *
import arcpy
import math
from RasterIO import *


class OurTreeManager(TreeManager.TreeManager):

    def __init__(self):
        TreeManager.TreeManager.__init__(self)

    def getsegmentbyprofilpt(self, row,col):
        for segment in self.treesegments():
            for ptprofil in segment.get_profile():
                if ptprofil.row == row and ptprofil.col == col:
                    return segment, ptprofil
        return None, None


    def browsepts(self):
        #   retour de la méthode : Générateur de ProfilePoint
        for l, m, n in self.__recursivetreepts(self.treeroot):
            yield l, m, n

    def uptodown_browsepts(self):
        #   retour de la méthode : Générateur de ProfilePoint
        for leaf in self.leaves():
            for l, m, n in self.__recursiveuptodowntreepts(leaf, None):
                yield l, m, n

    def __recursiveuptodowntreepts(self, treesegment, preccs):

        yield treesegment, preccs, treesegment.get_profile()[-1]

        for i in range(len(treesegment.get_profile())-2, -1, -1):
            yield treesegment, treesegment.get_profile()[i + 1], treesegment.get_profile()[i]

        if not treesegment.is_root():
            for l, m, n in self.__recursiveuptodowntreepts(treesegment.get_parent(), treesegment.get_profile()[0]):
                yield l, m, n



    def __recursivetreepts(self, treesegment):
        if treesegment.is_root():
            yield treesegment, None, treesegment.get_profile()[0]
        else:
            yield treesegment, treesegment.get_parent().get_profile()[-1], treesegment.get_profile()[0]
        for i in range(1, len(treesegment.get_profile())):
            yield treesegment, treesegment.get_profile()[i - 1], treesegment.get_profile()[i]
        for child in treesegment.get_childrens():
            for l, m, n in self.__recursivetreepts(child):
                yield l, m, n


def build_trees(flowdir, frompoint, dtype="SINGLE", **kwargs):

    trees = []
    segmentid = 0

    treated_pts = {}

    # Traitement effectué pour chaque point de départ
    frompointcursor = arcpy.da.SearchCursor(frompoint, ["SHAPE@", "OID@"])
    for frompoint in frompointcursor:

        # On prend l'objet géométrique (le point) associé à la ligne dans la table
        frompointshape = frompoint[0].firstPoint

        # Conversion des coordonnées
        currentcol = flowdir.XtoCol(frompointshape.X)
        currentrow = flowdir.YtoRow(frompointshape.Y)

        # Tests de sécurité pour s'assurer que le point de départ est à l'intérieurs des rasters
        intheraster = True
        if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
            intheraster = False
        elif (flowdir.getValue(currentrow, currentcol) != 1 and flowdir.getValue(currentrow, currentcol) != 2 and
                      flowdir.getValue(currentrow, currentcol) != 4 and flowdir.getValue(currentrow,
                                                                                         currentcol) != 8 and
                      flowdir.getValue(currentrow, currentcol) != 16 and flowdir.getValue(currentrow,
                                                                                          currentcol) != 32 and flowdir.getValue(
            currentrow, currentcol) != 64 and flowdir.getValue(currentrow, currentcol) != 128):
            intheraster = False

        segmentid += 1
        newtreeseg = OurTreeSegment(segmentid)


        # Traitement effectué sur chaque cellule le long de l'écoulement
        while (intheraster):


            dictdata = {}
            if dtype=="SINGLE":
                for paramname, param in kwargs.items():
                    dictdata[paramname] = param.getValue(currentrow, currentcol)
                ptprofile = ProfilePoint.ProfilePoint(currentrow, currentcol, 0, dictdata)
            else:
                # param must be a dictionary of RasterIO object (the data are a collection of rasters in a folder)
                for paramname, param in kwargs.items():
                    for raster_name, raster in param.items():
                        if not dictdata.has_key(raster_name):
                            dictdata[raster_name] = {}
                        dictdata[raster_name][paramname] = raster.getValue(currentrow, currentcol)
                ptprofile = ProfilePoint.ProfilePointMulti(currentrow, currentcol, 0, dictdata)
            ptprofile.X = flowdir.ColtoX(currentcol)
            ptprofile.Y = flowdir.RowtoY(currentrow)
            newtreeseg.add_ptprofile(ptprofile)
            treated_pts[(currentrow, currentcol)] = segmentid

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

            ptprofile.dist = currentdistance

            # Tests de sécurité pour s'assurer que l'on ne sorte pas des rasters
            if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
                intheraster = False
            elif (flowdir.getValue(currentrow, currentcol) != 1 and flowdir.getValue(currentrow,
                                                                                     currentcol) != 2 and
                          flowdir.getValue(currentrow, currentcol) != 4 and flowdir.getValue(currentrow,
                                                                                             currentcol) != 8 and
                          flowdir.getValue(currentrow, currentcol) != 16 and flowdir.getValue(currentrow,
                                                                                              currentcol) != 32 and flowdir.getValue(
                currentrow, currentcol) != 64 and flowdir.getValue(currentrow, currentcol) != 128):
                intheraster = False

            if intheraster:
                if (currentrow, currentcol) in treated_pts:
                    # Atteinte d'un confluent
                    nextcellsegment = treated_pts[(currentrow, currentcol)]
                    intheraster = False
                    # tree.get_treesegment(nextcellsegment).add_child(fp_tree)
                    # confluence = True
                    # confluenceid = nextcellsegment
                    segmentid += 1
                    # on cherche l'arbre et le segment que l'on vient de rejoindre
                    for tree in trees:
                        oldsegment, ptprofile = tree.getsegmentbyprofilpt(currentrow, currentcol)
                        if oldsegment is not None:
                            break
                    oldsegment.fork(newtreeseg, segmentid, ptprofile)



            else:
                tree = OurTreeManager()
                tree.treeroot = newtreeseg
                trees.append(tree)

    return trees