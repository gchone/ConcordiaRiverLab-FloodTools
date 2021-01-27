# -*- coding: utf-8 -*-


### Historique des versions ###
# v0.1 - Nov 2020 - Création. Inspiré de InterpolationProfilsD8D4.py de François Larouche-Tremblay


from tree.TreeSegment import *
from tree.ProfilePoint import *
import arcpy, os
import math
import numpy as np
import numpy.lib.recfunctions as rfn



class TreeManager(object):

    ### Instance attributes ###
    # net: a line shapefile (normally with M)
    # routeID_field: the name of the route ID field in the net shapefile


    def __init__(self):
        self.treeroot = None


    def treesegments(self):
        #   retour de la méthode : Générateur de TreeSegment
        for n in self.__recursivetreesegments(self.treeroot):
            yield n

    def treesegments_uptodown(self):
        #   retour de la méthode : Générateur de TreeSegment
        for leaf in self.leaves():
            for n in self.__recursivetreesegments_uptodown(leaf):
                yield n

    def __recursivetreesegments(self, treesegment):
        #   treesegment : TreeSegment - Segment à retourner, ainsi que ces enfants (segments amont)
        #   retour de la méthode : Générateur de TreeSegment
        yield treesegment
        for child in treesegment.get_childrens():
            for n in self.__recursivetreesegments(child):
                yield n

    def __recursivetreesegments_uptodown(self, treesegment):
        #   treesegment : TreeSegment - Segment à retourner, ainsi que son parent (segment aval)
        #   retour de la méthode : Générateur de TreeSegment
        yield treesegment
        if not treesegment.is_root():
            for n in self.__recursivetreesegments_uptodown(treesegment.get_parent()):
                yield n

    def get_treesegment(self, id):
        #   id : int - Identifiant d'un segment
        #   retour de la méthode : TreeSegment
        for segment in self.treesegments():
            if segment.id == id:
                return segment

    def leaves(self):
        #   retour de la méthode : liste de Segments (les extrémités amont)
        leaves = []
        for segment in self.treesegments():
            if segment.is_leaf():
                leaves.append(segment)
        return leaves

    def __str__(self):
        return str(self.treeroot)



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

        for i in range(len(treesegment.get_profile()) - 2, -1, -1):
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

    def treesegments_prioritize_by_attribute(self, cs_attribute):
        #   retour de la méthode : Générateur de TreeSegment
        for n in self.__recursivetreesegments_prioritize_by_attribute(self.treeroot, cs_attribute):
            yield n

    def __recursivetreesegments_prioritize_by_attribute(self, treesegment, cs_attribute):
        #   treesegment : TreeSegment - Segment à retourner, ainsi que ces enfants (segments amont)
        #   retour de la méthode : Générateur de TreeSegment
        yield treesegment
        # sorting upstream reaches by an attribute (from higher to lower)
        upstream_segments = list(treesegment.get_childrens())
        upstream_segments.sort(key=lambda segment: segment.get_profile()[0].getattr(cs_attribute), reverse=True)
        for child in upstream_segments:
            for n in self.__recursivetreesegments_prioritize_by_attribute(child, cs_attribute):
                yield n

    class __PointsData(object):

        def __init__(self, numpydata, id_field, dict_field):
            self.numpydata = numpydata
            self.dict_field = dict_field
            self.id_field = id_field

        def get_item(self, id, key):
            return self.numpydata[self.numpydata[self.id_field] == id][self.dict_field[key]][0]

    def load_points(self, sourcepoints, routeID_field, distance_field, dict_fields):
        """

        :param sourcepoints:
        :param routeID_field:
        :param distance_field:
        :param dict_fields:
        :return:
        """
        numpydata = arcpy.da.FeatureClassToNumPyArray(sourcepoints, ["OID@", routeID_field, distance_field, routeID_field].extend(dict_fields.values))
        self.__pointdata = self.__PointsData(numpydata, "OID@", dict_fields)


        # add ProfilePoints
        for segment in self.treesegments():
            listpts = np.sort(numpydata[numpydata[routeID_field] == segment.id], order=distance_field)
            segment.__ptsprofile=[]
            for pts in listpts:
                segment.__ptsprofile.append(ProfilePoint(pts))



    def interpolate(self, sourcepoints, value_field, source_meas_field, source_routeID_field, targetpoints, target_meas_field, target_routeID_field):
        """

        :param sourcepoints:
        :param value_field:
        :param source_meas_field:
        :param source_routeID_field:
        :param targetpoints:
        :param target_meas_field:
        :param target_routeID_field:
        :return:
        """
        # interpolate sourcepoints where the target points are
        # both data must be linear referenced on the network (ProjectOnRiverNetwork can be used)
        np_source = arcpy.da.FeatureClassToNumPyArray(sourcepoints, [value_field, source_meas_field, source_routeID_field])
        np_target = arcpy.da.FeatureClassToNumPyArray(targetpoints, [target_meas_field, target_routeID_field, "SHAPE@X", "SHAPE@Y"])

        results = None

        for segment in self.treesegments():
            sourcesort = np.sort(np_source[np_source[source_routeID_field] == segment.id], order=source_meas_field)

            if len(sourcesort)>0:
                # Do nothing if there are no source points in this reach
                if not segment.is_root():
                    # adding the most upstream point of the downstream reach
                    downstreamsort = np.sort(np_source[np_source[source_routeID_field] == segment.get_parent().id], order=source_meas_field)
                    if len(downstreamsort)>0:
                        firstdown = downstreamsort[0]
                        # chanching the measurement to fit the current reach
                        firstdown[source_meas_field] = firstdown[source_meas_field]+segment.length
                        sourcesort = np.concatenate(([firstdown], sourcesort), axis=0)

                if not segment.is_leaf():
                    # adding the most downstream point of the upstream reach (with the smallest value)
                    lastup = None
                    for upstreamreach in segment.get_childrens():
                        upstreamsort = np.sort(np_source[np_source[source_routeID_field] == upstreamreach.id], order=source_meas_field)
                        if len(upstreamsort)>0:
                            templastup = upstreamsort[len(upstreamsort)-1]
                            # put measurement to a negative value
                            templastup[source_meas_field] = templastup[source_meas_field]-upstreamreach.length
                            if lastup is None or templastup[value_field] < lastup[value_field]:
                                lastup = templastup
                    if lastup is not None:
                        sourcesort = np.concatenate((sourcesort, [lastup]), axis=0)


                targetsort = np.sort(np_target[np_target[target_routeID_field] == segment.id], order=target_meas_field)

                newtarget_values = np.interp(targetsort[target_meas_field], sourcesort[source_meas_field], sourcesort[value_field])
                seg_results = rfn.merge_arrays([targetsort, newtarget_values], flatten = True)


                if results is None:
                    results = seg_results
                else:
                    results = np.concatenate((results, seg_results), axis=0)

        return results




def __recursivebuildtree(treeseg, downstream_junction, np_junctions, check_orientation, np_net, netid_name, length_field):


    if check_orientation:
        # if the dowstreamn point is a "End" point, orientation is good (=True)
        treeseg.orientation = downstream_junction["ENDTYPE"] == "End"
    else:
        treeseg.length = np_net[np_net[netid_name] == treeseg.id][length_field][0]

    # Find the upstreams junction for the current reach
    condition1 = np_junctions["ORIG_FID"] == treeseg.id
    condition2 = np_junctions["FEAT_SEQ"] <> downstream_junction["FEAT_SEQ"]
    upstream_junction = np.extract(np.logical_and(condition1, condition2), np_junctions)[0]

    # Find other junctions at the same place
    condition1 = np_junctions["FEAT_SEQ"] == upstream_junction["FEAT_SEQ"]
    condition2 = np_junctions["ORIG_FID"] <> upstream_junction["ORIG_FID"]

    downstream_junctions = np.extract(np.logical_and(condition1, condition2), np_junctions)

    for downstream_junction in downstream_junctions:

            newtreeseg = TreeSegment(downstream_junction["ORIG_FID"])
            treeseg.add_child(newtreeseg)

            __recursivebuildtree(newtreeseg, downstream_junction, np_junctions, check_orientation,  np_net, netid_name, length_field)

    return



def build_trees(rivernet, routeID_field, length_field):
    __generic_build_trees(rivernet, routeID_field, oriented=True, downstream_reach_field=None, length_field=length_field)

def nonoriented_build_trees(rivernet, routeID_field, downstream_reach_field):
    __generic_build_trees(rivernet, routeID_field, oriented=False, downstream_reach_field=downstream_reach_field, length_field=None)

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
        np_net = arcpy.da.FeatureClassToNumPyArray(rivernet, [netid_name, downstream_reach_field])
        net_down_id = np.extract(np_net[downstream_reach_field] == 1, np_net)[netid_name]
        # select only the junction from this list
        condition2 = np.array([item in net_down_id for item in np_junctions["ORIG_FID"]])
    if oriented:
        # just take the 'End' ones
        np_net = arcpy.da.FeatureClassToNumPyArray(rivernet, [netid_name, length_field])
        condition2 = np_junctions["ENDTYPE"] == "End"
    downstream_junctions = np.extract(np.logical_and(condition, condition2), np_junctions)

    for downstream_junction in downstream_junctions:

            newtreeseg = TreeSegment(downstream_junction["ORIG_FID"])
            newtree = TreeManager()
            newtree.treeroot = newtreeseg

            newtree.net = rivernet
            newtree.routeID_field = routeID_field

            trees.append(newtree)

            __recursivebuildtree(newtreeseg, downstream_junction, np_junctions, not oriented, np_net, netid_name, length_field)

    arcpy.Delete_management(junctions)
    arcpy.Delete_management(junctions_table)

    return trees


