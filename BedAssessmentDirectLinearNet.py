# -*- coding: utf-8 -*-

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################


import os
import arcpy
import pickle
from RasterIO import *
from tree.RiverNetwork import *
from tree.TreeTools import *
#from Solver2 import *
from SolverDirect import *


def execute_BedAssessment(rivernet, points_coll, manning, upstream_s, messages):
    """
    Compute the bed assessment
    Require three attributes in the points collection points_coll: "wslidar", "Q", "width"
    Create a new attribute: "z"
    :param rivernet: The river network (instance of RiverNetwork)
    :param points_coll: The point collection (instance of Points_collection) storing the input data
    :param manning: Manning's n
    :param upstream_s: Upstream slope to be used as a upstream boundart condition (TO BE REMOVED)
    :param messages: ArcGIS Messages object
    :return:
    """

    # hardcoded parameter: Minimum difference of water surface elevation for backwater area
    delta_z_min = 0.01

    # TODO:
    # upstream_s : prendre la pente de la surface avec le point downstream.
    # when passing a second time on a downstream reach, stop if the bed calculated is close to the previously calculated one

    # First pass to identify backwater area
    backwater_pts = []
    length = 0
    prev_cs = None
    # TODO:
    # at confluences
    for reach in rivernet.browse_reaches():
        for cs in reach.browse_points(points_coll):
            if prev_cs is not None:
                if cs.wslidar <= prev_cs.wslidar:
                    backwater_pts.append(cs)
                    length += (cs.dist-prev_cs.dist)
                else:
                    cs.s_min = 0
                    for backcs in backwater_pts:
                        backcs.s_min = delta_z_min/length
                    length = 0
                    backwater_pts = []
            else:
                cs.s_min = 0
            prev_cs = cs

    # 1D hydraulic calculations
    for reach in rivernet.browse_reaches(orientation="UP_TO_DOWN"):
        # Looking for the upstream datapoint
        if reach.is_upstream_end():
            prev_cs = None
        # no else: if it's not an upstream reach the prev_cs is already good

        for cs in reach.browse_points(points_coll, orientation="UP_TO_DOWN"):
            cs.n = manning


            if prev_cs == None:

                # downstream cs calculation
                cs.s = upstream_s
                manning_solver(cs)

                cs.solver = "manning"
                cs.type = 0


            else:

                # if cs.wslidar < prev_cs.wslidar:
                __recursive_inverse1Dhydro(cs, prev_cs)

                # else:
                #     cs.ycrit = 0
                #     cs.z = -9999
                #     cs.v = 0
                #     cs.h = cs.wslidar
                #     cs.Fr = 0
                #     cs.solver = "infinite"
                #     cs.type = 2
                #     cs.s = 0

            prev_cs = cs

    return

def __recursive_inverse1Dhydro(cs, prev_cs):
    cs_solver(prev_cs, cs)
    cs.solver = "regular"
    cs.type = 1

    # Adding a cross-section if the Froude number varies too much
    if (cs.Fr - prev_cs.Fr) / prev_cs.Fr > 0.5 : #and prev_cs.dist - cs.dist > 0.01:
        # add a point in the middle
        if cs.reach == prev_cs.reach:
            newdist = (cs.dist + prev_cs.dist) / 2.
            newcs = cs.reach.add_point(newdist, 0, cs.points_collection)
            # TODO:
            # Temporary. Certainly not the cleanest way to proceed
            a = (cs.width - prev_cs.width) / (cs.dist - prev_cs.dist)
            newcs.width = a * newcs.dist + cs.width - a * cs.dist
            a = (cs.Q - prev_cs.Q) / (cs.dist - prev_cs.dist)
            newcs.Q = a * newcs.dist + cs.Q - a * cs.dist
            a = (cs.wslidar - prev_cs.wslidar) / (cs.dist - prev_cs.dist)
            newcs.wslidar = a* newcs.dist + cs.wslidar - a* cs.dist
            newcs.n = cs.n
            newcs.s_min = 0

            __recursive_inverse1Dhydro(newcs, prev_cs)
            newcs.solver = "added"
            cs.type = 3
            __recursive_inverse1Dhydro(cs, newcs)

        else:
            # TODO:
            # case where the interpolation takes place between two reaches
            pass

