# -*- coding: utf-8 -*-

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################


import os
import arcpy

from tree.RiverNetwork import *
from tree.TreeTools import *

from SolverDirect import *


def execute_BedAssessment(route, route_RID_field, route_order_field, routelinks, points, points_IDfield, points_RIDfield, points_distfield, points_Qfield, points_Wfield, points_WSfield, points_DEMfield, manning, output_pts, messages, anchored_z_field=None):

    rivernet = RiverNetwork()
    rivernet.dict_attr_fields['id'] = route_RID_field
    rivernet.dict_attr_fields['order'] = route_order_field
    rivernet.load_data(route, routelinks)

    points_coll = Points_collection(rivernet, "data")
    points_coll.dict_attr_fields['id'] = points_IDfield
    points_coll.dict_attr_fields['reach_id'] = points_RIDfield
    points_coll.dict_attr_fields['dist'] = points_distfield
    points_coll.dict_attr_fields['wslidar'] = points_WSfield
    points_coll.dict_attr_fields['Q'] = points_Qfield
    points_coll.dict_attr_fields['width'] = points_Wfield
    points_coll.dict_attr_fields['DEM'] = points_DEMfield
    if anchored_z_field is not None:
        points_coll.dict_attr_fields['anchor'] = anchored_z_field
    points_coll.load_table(points)


    # Following code was changed:
    # Instead of imposing a minimum slope that varies with the length of the backwater ares (defined as no-slope area),
    #   a constant minimum slope is imposed everywhere
    min_slope = 0.0001

    for reach in rivernet.browse_reaches_down_to_up():
        lastpoint = reach.get_last_point(points_coll)
        if reach.is_downstream_end():
            prev_cs = None
        else:
            prev_cs = reach.get_downstream_reach().get_last_point(points_coll)
        for cs in reach.browse_points(points_coll):
            if reach.is_upstream_end() and cs == lastpoint:
                if cs.reach == prev_cs.reach:
                    localdist = (cs.dist - prev_cs.dist)
                else:
                    localdist = prev_cs.reach.length - prev_cs.dist + cs.dist
                cs.s = max(min_slope, (cs.wslidar-prev_cs.wslidar)/localdist) # Compute upstream boundary condition
            prev_cs = cs

    # # hardcoded parameter: Minimum difference of water surface elevation for backwater area
    # delta_z_min = 0.01
    #
    # # First pass to identify minimum slope for backwater area and upstream boundary condition
    # backwater_pts = []
    # length = 0
    # prev_cs = None
    # for reach in rivernet.browse_reaches_down_to_up():
    #     lastpoint = reach.get_last_point(points_coll)
    #     for cs in reach.browse_points(points_coll):
    #         if prev_cs is not None:
    #             if cs.reach == prev_cs.reach:
    #                 localdist = (cs.dist - prev_cs.dist)
    #             else:
    #                 localdist = prev_cs.reach.length - prev_cs.dist + cs.dist
    #
    #             if cs.wslidar <= prev_cs.wslidar:
    #                 backwater_pts.append(cs)
    #                 length += localdist
    #             else:
    #                 cs.s_min = 0
    #                 for backcs in backwater_pts:
    #                     backcs.s_min = delta_z_min/length
    #                 length = 0
    #                 backwater_pts = []
    #         else:
    #             cs.s_min = 0
    #         if reach.is_upstream_end():
    #             if cs == lastpoint:
    #                 for backcs in backwater_pts:
    #                     backcs.s_min = delta_z_min/length
    #                 length = 0
    #                 backwater_pts = []
    #                 cs.s = max(cs.s_min, (cs.wslidar-prev_cs.wslidar)/localdist) # Compute upstream boundary condition
    #         prev_cs = cs # ERREUR A CORRIGER : CHANGEMENT DE REACH

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
            cs.anchored = False
            if anchored_z_field is not None and cs.anchor != -9999: # Imposed bed elevation
                cs.solver = "anchor"
                cs.z = cs.anchor
                cs.y = cs.wslidar - cs.z
                if cs.y <= 0:
                    messages.addWarningMessage(
                        "Imposed bed elevation above water surface at reach " + str(cs.reach.id) + ", distance " + str(
                            cs.dist))
                    cs.y = (cs.Q / (cs.width * g ** 0.5)) ** (2. / 3.) # critical depth used as a place holder
                    cs.z = cs.wslidar - cs.y

                cs.R = (cs.width * cs.y) / (cs.width + 2 * cs.y)
                cs.v = cs.Q / (cs.width * cs.y)
                cs.s = (cs.n ** 2 * cs.v ** 2) / (cs.R ** (4. / 3.))
                cs.anchored = True
                cs.h = cs.wslidar + cs.v ** 2 / (2 * g)
                cs.Fr = cs.v / (g * cs.y) ** 0.5
            else:
                if prev_cs == None:
                    manning_solver(cs)
                    cs.solver = "manning up"
                    cs.type = 0

                else:
                    if prev_cs.DEM != cs.DEM:
                        cs.s = prev_cs.s
                        manning_solver(cs)
                        cs.solver = "manning"
                        cs.type = 0
                    else:
                        cs.solver = "regular"
                        cs.type = 1
                        __recursive_inverse1Dhydro(cs, prev_cs, min_slope)

            prev_cs = cs

        done_reaches.append(reach)

    points_coll.add_SavedVariable("solver", "str", 10)
    points_coll.add_SavedVariable("y", "float")
    points_coll.add_SavedVariable("R", "float")
    points_coll.add_SavedVariable("v", "float")
    points_coll.add_SavedVariable("z", "float")
    points_coll.add_SavedVariable("h", "float")
    points_coll.add_SavedVariable("s", "float")
    points_coll.add_SavedVariable("Fr", "float")
    points_coll.save_points(output_pts)

    return

def __recursive_inverse1Dhydro(cs, prev_cs, min_slope):

    flag = cs_solver(prev_cs, cs, min_slope)
    if flag != 1:
        # The solver issued a warning
        # It's usually because no solution was found
        # The last attempt is the closes value found, so we keep it
        cs.solver = "error"
        cs.type = -999

    if cs.reach == prev_cs.reach:
        localdist = (prev_cs.dist - cs.dist)
    else:
        localdist = cs.reach.length - cs.dist + prev_cs.dist

    # Adding a cross-section if the Froude number varies too much
    if (cs.Fr - prev_cs.Fr) / prev_cs.Fr > 0.5 and localdist > 0.1: # Minimum 10cm between cs
        if cs.reach == prev_cs.reach:
            newcs = cs.reach.add_point((cs.dist + prev_cs.dist) / 2., cs.points_collection)
        else:
            # case where the interpolation takes place between two reaches
            if localdist / 2. < prev_cs.dist:
                # point is in the upstream reach (prev_cs reach)
                newcs = prev_cs.reach.add_point(localdist / 2., cs.points_collection)
            else:
                newcs = cs.reach.add_point(cs.dist + localdist / 2., cs.points_collection)

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
        newcs.DEM = prev_cs.DEM
        newcs.anchored = False
        __recursive_inverse1Dhydro(newcs, prev_cs, min_slope)
        newcs.solver = "added"
        newcs.type = 3
        __recursive_inverse1Dhydro(cs, newcs, min_slope)

    return

