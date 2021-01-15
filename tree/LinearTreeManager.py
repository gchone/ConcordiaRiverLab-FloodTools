# coding: latin-1


### Historique des versions ###
# v0.1 - Nov 2020 - Création. Inspiré de InterpolationProfilsD8D4.py de François Larouche-Tremblay


import tree.TreeManager as TreeManager
from tree.LinearTreeSegment import *
import arcpy, os
import math
import numpy as np
import numpy.lib.recfunctions as rfn



class LinearTreeManager(TreeManager.TreeManager):

    ### Instance attributes ###
    # net: a line shapefile (normally with M)
    # routeID_field: the name of the route ID field in the net shapefile


    def __init__(self):
        TreeManager.TreeManager.__init__(self)


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

            newtreeseg = LinearTreeSegment(downstream_junction["ORIG_FID"])
            treeseg.add_child(newtreeseg)

            __recursivebuildtree(newtreeseg, downstream_junction, np_junctions, check_orientation,  np_net, netid_name, length_field)

    return



def build_trees(rivernet, routeID_field, length_field):
    __generic_build_trees(rivernet, routeID_field, oriented=True, downstream_reach_field=None, length_field=length_field)

def nonoriented_build_trees(rivernet, routeID_field, downstream_reach_field):
    __generic_build_trees(rivernet, routeID_field, oriented=False, downstream_reach_field=downstream_reach_field, length_field=None)

def __generic_build_trees(rivernet, routeID_field, downstream_reach_field, length_field):
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

            newtreeseg = LinearTreeSegment(downstream_junction["ORIG_FID"])
            newtree = LinearTreeManager()
            newtree.treeroot = newtreeseg

            newtree.net = rivernet
            newtree.routeID_field = routeID_field

            trees.append(newtree)

            __recursivebuildtree(newtreeseg, downstream_junction, np_junctions, not oriented, np_net, netid_name, length_field)

    arcpy.Delete_management(junctions)
    arcpy.Delete_management(junctions_table)

    return trees



