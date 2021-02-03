# coding: latin-1

# Fichier TreeManager.py
# v0.0.2 - 24/10/2017

### Contenu ###
# classe OurTreeManager : Classe de gestion générique d'un arbre avec OurTreeSegments

### Historique des versions ###
# v0.0.1 - 13/11/2018 - Création
# v0.1 - 22/05/2020 - Modification pour création d'arbre multiples
# v1.0 - Nov 2020 - Ajout de dossier en paramètre de données (kwargs): Crée un dictionnaire avec comme clé le nom de chaque raster du dossier
#  Ajout de X et Y pour les points. Ajout de la recherche de points amont avec une donnée.


import tree.TreeManager as TreeManager
from tree.OurTreeSegment import *
import arcpy
import math
from RasterIO import *
import numpy as np


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

    # def browsepts_bypriority(self, priority_attribute):
    #     #   retour de la méthode : Générateur de ProfilePoint
    #     for l, m, n in self.__recursivetreepts_bypriority(self.treeroot, priority_attribute):
    #         yield l, m, n

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

    def points_up_with_data(self, segment, cs, cs_attribute, cs_attribute_nodata_value):
        csposition = segment.get_ptprofile_pos(cs)
        for csup in self.__recursive_points_up_with_data(segment, csposition, cs_attribute, cs_attribute_nodata_value):
            yield csup

    def __recursive_points_up_with_data(self, segment, csposition, cs_attribute, cs_attribute_nodata_value):
        foundup = False
        pos = 0
        for csup in segment.get_profile():
            if pos > csposition and not foundup:
                if hasattr(csup, cs_attribute) and getattr(csup, cs_attribute) != cs_attribute_nodata_value:
                    foundup = True
                    yield csup
            pos += 1
        if not foundup:
            for child in segment.get_childrens():
                for csup in self.__recursive_points_up_with_data(child, -1, cs_attribute, cs_attribute_nodata_value):
                    yield csup

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


    # def __recursivetreepts_bypriority(self, treesegment, priority_attribute):
    #     if treesegment.is_root():
    #         yield treesegment, None, treesegment.get_profile()[0]
    #     else:
    #         yield treesegment, treesegment.get_parent().get_profile()[-1], treesegment.get_profile()[0]
    #     for i in range(1, len(treesegment.get_profile())):
    #         yield treesegment, treesegment.get_profile()[i - 1], treesegment.get_profile()[i]
    #     listchildren = []
    #     lastprofilevalue= treesegment.get_profile()[-1].getattr(priority_attribute)
    #     for child in treesegment.get_childrens():
    #         listchildren.append((child, abs(child.get_profile()[0].getattr(priority_attribute)-lastprofilevalue)))
    #         #sort list by min dif
    #         for l, m, n in self.__recursivetreepts_bypriority(child, priority_attribute):
    #             yield l, m, n
    #



    def load_multipoints(self, sourcepoints_dir, routeID_field, distance_field, X_field, Y_field, dict_fields):

        arcpy.env.workspace = sourcepoints_dir
        sourcepointslist = arcpy.ListFeatureClasses()

        # add ProfilePoints
        for segment in self.treesegments():
            #segment.__ptsprofile = []

            dictdata_byptsid = {}
            firstsourcepoints = True

            for sourcepoints in sourcepointslist:
                sourcepointsname = os.path.splitext(sourcepoints)[0]

                sourcepointsid_name = arcpy.Describe(sourcepoints).OIDFieldName
                listfields = [sourcepointsid_name, routeID_field, distance_field, X_field, Y_field]
                listfields.extend(dict_fields.values())
                numpydata = arcpy.da.FeatureClassToNumPyArray(sourcepoints, listfields)
                listpts = numpydata[numpydata[routeID_field] == segment.id]

                for pts in listpts:
                    if firstsourcepoints:
                        dictdata = {}
                        dictdata_byptsid[pts[sourcepointsid_name]] = dictdata
                    else:
                        dictdata = dictdata_byptsid[pts[sourcepointsid_name]]
                    dictdata[sourcepointsname] = {}
                    for key, value in dict_fields.items():
                        dictdata[sourcepointsname][key] = pts[value]
                firstsourcepoints = False
                lastlistpts = listpts

            for ptid, ptdictdata in dictdata_byptsid.items():
                numpyrow = lastlistpts[lastlistpts[sourcepointsid_name] == ptid]
                ptprofile = ProfilePoint.ProfilePointMulti(numpyrow[X_field][0], numpyrow[Y_field][0], numpyrow[distance_field][0], ptdictdata)
                segment.add_ptprofile_inorder(ptprofile)

    def save_multipoints(self, targetpoints_dir, value_name, spatial_ref):

        dict_save = {}
        for segment in self.treesegments():
            for pt in segment.get_profile():
                for rastername, data in pt.data_dict.items():
                    if not dict_save.has_key(rastername):
                        dict_save[rastername] = []
                    if hasattr(data, value_name):
                        dict_save[rastername].append([pt.X, pt.Y, getattr(data, value_name)])

        for key, data in dict_save.items():

            arcpy.CreateFeatureclass_management(targetpoints_dir,
                                                os.path.basename(key), "POINT",
                                                spatial_reference=spatial_ref)
            str_output_points = os.path.join(targetpoints_dir, key+".shp")
            arcpy.AddField_management(str_output_points, "value", "FLOAT")
            pointcursor = arcpy.da.InsertCursor(str_output_points, ["SHAPE@XY", "value"])
            for X, Y, value in data:
                pointcursor.insertRow([(X, Y), value])




def __recursivebuildtree(treeseg, downstream_junction, np_junctions, check_orientation, np_net, netid_name, length_field, routeID_field):


    if check_orientation:
        # if the dowstreamn point is a "End" point, orientation is good (=True)
        treeseg.orientation = downstream_junction["ENDTYPE"] == "End"
    else:
        treeseg.length = np_net[np_net[netid_name] == treeseg.shapeid][length_field][0]

    # Find the upstreams junction for the current reach
    condition1 = np_junctions["ORIG_FID"] == treeseg.shapeid
    condition2 = np_junctions["FEAT_SEQ"] <> downstream_junction["FEAT_SEQ"]
    upstream_junction = np.extract(np.logical_and(condition1, condition2), np_junctions)[0]

    # Find other junctions at the same place
    condition1 = np_junctions["FEAT_SEQ"] == upstream_junction["FEAT_SEQ"]
    condition2 = np_junctions["ORIG_FID"] <> upstream_junction["ORIG_FID"]

    downstream_junctions = np.extract(np.logical_and(condition1, condition2), np_junctions)

    for downstream_junction in downstream_junctions:

        id = np_net[np_net[netid_name] == downstream_junction["ORIG_FID"]][routeID_field][0]
        newtreeseg = OurTreeSegment(id)
        newtreeseg.shapeid = downstream_junction["ORIG_FID"]
        treeseg.add_child(newtreeseg)

        __recursivebuildtree(newtreeseg, downstream_junction, np_junctions, check_orientation,  np_net, netid_name, length_field, routeID_field)

    return



def build_trees(rivernet, routeID_field, length_field):
    return __generic_build_trees(rivernet, routeID_field, oriented=True, downstream_reach_field=None, length_field=length_field)

def nonoriented_build_trees(rivernet, routeID_field, downstream_reach_field):
    return __generic_build_trees(rivernet, routeID_field, oriented=False, downstream_reach_field=downstream_reach_field, length_field=None)

def __generic_build_trees(rivernet, routeID_field, oriented, downstream_reach_field, length_field):
    """

    :param rivernet:
    :param routeID_field:
    :param oriented:
    :param downstream_reach_field:
    :param length_field:
    :return:
    """
    # usually used with an orientated network. Provide length_field in this case
    # can also be used with a non-orientated network. Provide a downstream_reach_field in this case (1=downstream end of the network, 0 elsewhere)

    trees = []

    # Create Junction points: two points created by reach, at both end of the line
    # (done separately with "END" and "START", rather than with "BOTH_ENDS", to keep track of what point is at which extremity)
    with arcpy.EnvManager(outputMFlag="Disabled"):
        with arcpy.EnvManager(outputZFlag="Disabled"):
            # Do not included Z and M values in the points, as it will mess with the grouping by Shape step (it should only be based on X and Y position)
            junctions_end = arcpy.CreateScratchName("net", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
            arcpy.FeatureVerticesToPoints_management(rivernet, junctions_end, "END")
            junctions_start = arcpy.CreateScratchName("net", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
            arcpy.FeatureVerticesToPoints_management(rivernet, junctions_start, "START")
    arcpy.AddField_management(junctions_end, "ENDTYPE", "TEXT", field_length=10)
    arcpy.AddField_management(junctions_start, "ENDTYPE", "TEXT", field_length=10)
    arcpy.CalculateField_management(junctions_end, "ENDTYPE", "'End'", "PYTHON")
    arcpy.CalculateField_management(junctions_start, "ENDTYPE", "'Start'", "PYTHON")
    junctions = arcpy.CreateScratchName("net", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
    arcpy.Merge_management([junctions_end, junctions_start], junctions)
    arcpy.Delete_management(junctions_end)
    arcpy.Delete_management(junctions_start)
    junctionid_name = arcpy.Describe(junctions).OIDFieldName

    #   Add a id ("FEAT_SEQ") to the junction grouping junctions at the same place (same place = same id))
    junctions_table = arcpy.CreateScratchName("net", data_type="ArcInfoTable", workspace=arcpy.env.scratchWorkspace)
    arcpy.FindIdentical_management(junctions, junctions_table, ["Shape"])
    arcpy.JoinField_management(junctions, junctionid_name, junctions_table, "IN_FID")
    np_junctions = arcpy.da.FeatureClassToNumPyArray(junctions, [junctionid_name, "ORIG_FID", "FEAT_SEQ", "ENDTYPE"])


    # Find downstream ends
    # count the number of junctions at the same place
    u, indices, count = np.unique(np_junctions["FEAT_SEQ"], return_index=True, return_counts=True)
    # select only the ones with one junction only
    condition = np.array([item in u[count == 1] for item in np_junctions["FEAT_SEQ"]])
    netid_name = arcpy.Describe(rivernet).OIDFieldName
    if not oriented:
        # get a list of id of downstream reaches
        np_net = arcpy.da.FeatureClassToNumPyArray(rivernet, [netid_name, downstream_reach_field, routeID_field])
        net_down_id = np.extract(np_net[downstream_reach_field] == 1, np_net)[netid_name]
        # select only the junction from this list
        condition2 = np.array([item in net_down_id for item in np_junctions["ORIG_FID"]])
    if oriented:
        # just take the 'End' ones
        np_net = arcpy.da.FeatureClassToNumPyArray(rivernet, [netid_name, length_field, routeID_field])
        condition2 = np_junctions["ENDTYPE"] == "End"
    downstream_junctions = np.extract(np.logical_and(condition, condition2), np_junctions)



    for downstream_junction in downstream_junctions:

        id = np_net[np_net[netid_name] == downstream_junction["ORIG_FID"]][routeID_field][0]
        newtreeseg = OurTreeSegment(id)
        newtree = OurTreeManager()
        newtree.treeroot = newtreeseg
        newtreeseg.shapeid = downstream_junction["ORIG_FID"]
        newtree.net = rivernet
        #newtree.routeID_field = routeID_field

        trees.append(newtree)

        __recursivebuildtree(newtreeseg, downstream_junction, np_junctions, not oriented, np_net, netid_name, length_field, routeID_field)

    arcpy.Delete_management(junctions)
    arcpy.Delete_management(junctions_table)

    return trees


#
# def build_trees(flowdir, frompoint, dtype="SINGLE", **kwargs):
#
#     trees = []
#     segmentid = 0
#
#     treated_pts = {}
#
#     # Traitement effectué pour chaque point de départ
#     frompointcursor = arcpy.da.SearchCursor(frompoint, ["SHAPE@", "OID@"])
#     for frompoint in frompointcursor:
#
#         # On prend l'objet géométrique (le point) associé à la ligne dans la table
#         frompointshape = frompoint[0].firstPoint
#
#         # Conversion des coordonnées
#         currentcol = flowdir.XtoCol(frompointshape.X)
#         currentrow = flowdir.YtoRow(frompointshape.Y)
#
#         # Tests de sécurité pour s'assurer que le point de départ est à l'intérieurs des rasters
#         intheraster = True
#         if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
#             intheraster = False
#         elif (flowdir.getValue(currentrow, currentcol) != 1 and flowdir.getValue(currentrow, currentcol) != 2 and
#                       flowdir.getValue(currentrow, currentcol) != 4 and flowdir.getValue(currentrow,
#                                                                                          currentcol) != 8 and
#                       flowdir.getValue(currentrow, currentcol) != 16 and flowdir.getValue(currentrow,
#                                                                                           currentcol) != 32 and flowdir.getValue(
#             currentrow, currentcol) != 64 and flowdir.getValue(currentrow, currentcol) != 128):
#             intheraster = False
#
#         segmentid += 1
#         newtreeseg = OurTreeSegment(segmentid)
#
#
#         # Traitement effectué sur chaque cellule le long de l'écoulement
#         while (intheraster):
#
#
#             dictdata = {}
#             if dtype=="SINGLE":
#                 for paramname, param in kwargs.items():
#                     dictdata[paramname] = param.getValue(currentrow, currentcol)
#                 ptprofile = ProfilePoint.ProfilePoint(currentrow, currentcol, 0, dictdata)
#             else:
#                 # param must be a dictionary of RasterIO object (the data are a collection of rasters in a folder)
#                 for paramname, param in kwargs.items():
#                     for raster_name, raster in param.items():
#                         if not dictdata.has_key(raster_name):
#                             dictdata[raster_name] = {}
#                         dictdata[raster_name][paramname] = raster.getValue(currentrow, currentcol)
#                 ptprofile = ProfilePoint.ProfilePointMulti(currentrow, currentcol, 0, dictdata)
#             ptprofile.X = flowdir.ColtoX(currentcol)
#             ptprofile.Y = flowdir.RowtoY(currentrow)
#             newtreeseg.add_ptprofile(ptprofile)
#             treated_pts[(currentrow, currentcol)] = segmentid
#
#             # On cherche le prochain point à partir du flow direction
#             direction = flowdir.getValue(currentrow, currentcol)
#             if (direction == 1):
#                 currentcol = currentcol + 1
#                 currentdistance = flowdir.raster.meanCellWidth
#             if (direction == 2):
#                 currentcol = currentcol + 1
#                 currentrow = currentrow + 1
#                 currentdistance = math.sqrt(
#                     flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)
#             if (direction == 4):
#                 currentrow = currentrow + 1
#                 currentdistance = flowdir.raster.meanCellHeight
#             if (direction == 8):
#                 currentcol = currentcol - 1
#                 currentrow = currentrow + 1
#                 currentdistance = math.sqrt(
#                     flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)
#             if (direction == 16):
#                 currentcol = currentcol - 1
#                 currentdistance = flowdir.raster.meanCellWidth
#             if (direction == 32):
#                 currentcol = currentcol - 1
#                 currentrow = currentrow - 1
#                 currentdistance = math.sqrt(
#                     flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)
#             if (direction == 64):
#                 currentrow = currentrow - 1
#                 currentdistance = flowdir.raster.meanCellHeight
#             if (direction == 128):
#                 currentcol = currentcol + 1
#                 currentrow = currentrow - 1
#                 currentdistance = math.sqrt(
#                     flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)
#
#             ptprofile.dist = currentdistance
#
#             # Tests de sécurité pour s'assurer que l'on ne sorte pas des rasters
#             if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
#                 intheraster = False
#             elif (flowdir.getValue(currentrow, currentcol) != 1 and flowdir.getValue(currentrow,
#                                                                                      currentcol) != 2 and
#                           flowdir.getValue(currentrow, currentcol) != 4 and flowdir.getValue(currentrow,
#                                                                                              currentcol) != 8 and
#                           flowdir.getValue(currentrow, currentcol) != 16 and flowdir.getValue(currentrow,
#                                                                                               currentcol) != 32 and flowdir.getValue(
#                 currentrow, currentcol) != 64 and flowdir.getValue(currentrow, currentcol) != 128):
#                 intheraster = False
#
#             if intheraster:
#                 if (currentrow, currentcol) in treated_pts:
#                     # Atteinte d'un confluent
#                     nextcellsegment = treated_pts[(currentrow, currentcol)]
#                     intheraster = False
#                     # tree.get_treesegment(nextcellsegment).add_child(fp_tree)
#                     # confluence = True
#                     # confluenceid = nextcellsegment
#                     segmentid += 1
#                     # on cherche l'arbre et le segment que l'on vient de rejoindre
#                     for tree in trees:
#                         oldsegment, ptprofile = tree.getsegmentbyprofilpt(currentrow, currentcol)
#                         if oldsegment is not None:
#                             break
#                     oldsegment.fork(newtreeseg, segmentid, ptprofile)
#
#
#
#             else:
#                 tree = OurTreeManager()
#                 tree.treeroot = newtreeseg
#                 trees.append(tree)
#
#     return trees