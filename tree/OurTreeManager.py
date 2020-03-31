# coding: latin-1

# Fichier TreeManager.py
# v0.0.2 - 24/10/2017

### Contenu ###
# classe OurTreeManager : Classe de gestion g�n�rique d'un arbre avec OurTreeSegments

### Historique des versions ###
# v0.0.1 - 13/11/2018 - Cr�ation



import TreeManager
from OurTreeSegment import *
import arcpy
import math


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
        #   retour de la m�thode : G�n�rateur de ProfilePoint
        for l, m, n in self.__recursivetreepts(self.treeroot):
            yield l, m, n

    def uptodown_browsepts(self):
        #   retour de la m�thode : G�n�rateur de ProfilePoint
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


    def build_tree(self, flowdir, frompoint, **kwargs):
        segmentid = 0

        treated_pts = {}

        # Traitement effectu� pour chaque point de d�part
        frompointcursor = arcpy.da.SearchCursor(frompoint, ["SHAPE@", "OID@"])
        for frompoint in frompointcursor:

            # On prend l'objet g�om�trique (le point) associ� � la ligne dans la table
            frompointshape = frompoint[0].firstPoint

            # Conversion des coordonn�es
            currentcol = flowdir.XtoCol(frompointshape.X)
            currentrow = flowdir.YtoRow(frompointshape.Y)

            # Tests de s�curit� pour s'assurer que le point de d�part est � l'int�rieurs des rasters
            intheraster = True
            if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
                intheraster = False
            elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                          flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow,
                                                                                             currentcol) <> 8 and
                          flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow,
                                                                                              currentcol) <> 32 and flowdir.getValue(
                currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
                intheraster = False

            segmentid += 1
            newtreeseg = OurTreeSegment(segmentid)

            print "fp: " + str(frompoint[1]) + " / id: " + str(segmentid)

            # Traitement effectu� sur chaque cellule le long de l'�coulement
            while (intheraster):


                dictdata = {}
                for rastername, raster in kwargs.items():
                    dictdata[rastername] = raster.getValue(currentrow, currentcol)

                ptprofile = ProfilePoint.ProfilePoint(currentrow, currentcol, 0, dictdata)
                newtreeseg.add_ptprofile(ptprofile)
                treated_pts[(currentrow, currentcol)] = segmentid

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

                ptprofile.dist = currentdistance

                # Tests de s�curit� pour s'assurer que l'on ne sorte pas des rasters
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

                if intheraster:
                    if treated_pts.has_key((currentrow, currentcol)):
                        # Atteinte d'un confluent
                        nextcellsegment = treated_pts[(currentrow, currentcol)]
                        intheraster = False
                        # tree.get_treesegment(nextcellsegment).add_child(fp_tree)
                        # confluence = True
                        # confluenceid = nextcellsegment
                        segmentid += 1
                        oldsegment, ptprofile = self.getsegmentbyprofilpt(currentrow, currentcol)
                        oldsegment.fork(newtreeseg, segmentid, ptprofile)



                else:
                    # tree.treeroot = fp_tree
                    self.treeroot = newtreeseg