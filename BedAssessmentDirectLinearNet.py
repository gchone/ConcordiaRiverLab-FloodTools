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

    # First pass to identify minimum slope for backwater area and upstream boundary condition
    backwater_pts = []
    length = 0
    prev_cs = None
    for reach in rivernet.browse_reaches_down_to_up():
        lastpoint = reach.get_last_point(points_coll)
        for cs in reach.browse_points(points_coll):
            if prev_cs is not None:
                if cs.reach == prev_cs.reach:
                    localdist = (cs.dist - prev_cs.dist)
                else:
                    localdist = prev_cs.reach.length - prev_cs.dist + cs.dist

                if cs.wslidar <= prev_cs.wslidar:
                    backwater_pts.append(cs)
                    length += localdist
                else:
                    cs.s_min = 0
                    for backcs in backwater_pts:
                        backcs.s_min = delta_z_min/length
                    length = 0
                    backwater_pts = []
            else:
                cs.s_min = 0
            if reach.is_upstream_end():
                if cs == lastpoint:
                    for backcs in backwater_pts:
                        backcs.s_min = delta_z_min/length
                    length = 0
                    backwater_pts = []
                    cs.s = max(cs.s_min, (cs.wslidar-prev_cs.wslidar)/localdist)
            prev_cs = cs

    # adding the 'order' attribute to reaches according to discharge
    rivernet.order_reaches_by_discharge(points_coll, "Q")
    # Current behaviour is to process main stream in priority (based on discharge)
    # Process is stopped when meeting an already-processed reach (bathymetry is never computed twice)

    # 1D hydraulic calculations
    stopper = BrowsingStopper()
    done_reaches = []
    for reach in rivernet.browse_reaches_up_to_down(prioritize_reach_attribute="order", stopper=stopper):
        # Looking for the upstream datapoint
        if reach.is_upstream_end():
            prev_cs = None
        # no else: if it's not an upstream reach the prev_cs is already good
        if reach in done_reaches:
            stopper.break_generator = True

        for cs in reach.browse_points(points_coll, orientation="UP_TO_DOWN"):
            cs.n = manning

            if prev_cs == None:
                manning_solver(cs)
                cs.solver = "manning"
                cs.type = 0

            else:
                if prev_cs.DEM != cs.DEM:
                    cs.s = prev_cs.s
                    manning_solver(cs)
                    cs.solver = "manning"
                    cs.type = 0
                else:
                    __recursive_inverse1Dhydro(cs, prev_cs)

            prev_cs = cs

        done_reaches.append(reach)

    return

def __recursive_inverse1Dhydro(cs, prev_cs):



    flag = cs_solver(prev_cs, cs)
    if flag != 1:
        # The solver issued a warning
        # It's usually because no solution was found
        # The last attempt is the closes value found, so we keep it
        cs.solver = "error"
        cs.type = -999
    else:
        cs.solver = "regular"
        cs.type = 1


    # Adding a cross-section if the Froude number varies too much
    if prev_cs.Fr > 0 and (cs.Fr - prev_cs.Fr) / prev_cs.Fr > 0.5 and cs.dist - prev_cs.dist > 0.1:
        # add a point in the middle
        if cs.reach == prev_cs.reach:
            newcs = cs.reach.add_point((cs.dist + prev_cs.dist) / 2., 0, cs.points_collection)
        else:
            # case where the interpolation takes place between two reaches
            downdist = prev_cs.reach.length - prev_cs.dist
            totaldist = downdist + cs.dist
            if totaldist / 2. < cs.dist:
                newcs = cs.reach.add_point(totaldist / 2., 0, cs.points_collection)
            else:
                newcs = prev_cs.reach.add_point(prev_cs.dist + totaldist / 2., 0, cs.points_collection)

        # Linear interpolation of width, discharge and water surface.
        # Although more accurate spatialization could be done, this is deemed accurate enough
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
        newcs.type = 3
        __recursive_inverse1Dhydro(cs, newcs)



