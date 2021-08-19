# -*- coding: utf-8 -*-

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################


import os
import arcpy

from Solver1Dnormal import *
from tree.TreeTools import *
from tree.RiverNetwork import *

def execute_Simple1Dhydraulic(route, route_RID_field, route_order_field, routelinks, points, points_IDfield, points_RIDfield, points_distfield,
     points_Qfield, points_Wfield, points_z_field, points_DEMfield, manning, downstream_s, output_pts, messages):

    rivernet = RiverNetwork()
    rivernet.dict_attr_fields['id'] = route_RID_field
    rivernet.dict_attr_fields['order'] = route_order_field
    rivernet.load_data(route, routelinks)

    points_coll = Points_collection(rivernet, "data")
    points_coll.dict_attr_fields['id'] = points_IDfield
    points_coll.dict_attr_fields['reach_id'] = points_RIDfield
    points_coll.dict_attr_fields['dist'] = points_distfield
    points_coll.dict_attr_fields['z'] = points_z_field
    points_coll.dict_attr_fields['Q'] = points_Qfield
    points_coll.dict_attr_fields['width'] = points_Wfield
    points_coll.dict_attr_fields['DEM'] = points_DEMfield

    points_coll.load_table(points)

    points_coll.add_SavedVariable("solver", "str", 10)
    points_coll.add_SavedVariable("y", "float")
    points_coll.add_SavedVariable("R", "float")
    points_coll.add_SavedVariable("v", "float")
    points_coll.add_SavedVariable("z", "float")
    points_coll.add_SavedVariable("h", "float")
    points_coll.add_SavedVariable("s", "float")
    points_coll.add_SavedVariable("Fr", "float")

    for reach in rivernet.browse_reaches_down_to_up():
        # Looking for the upstream datapoint
        if reach.is_downstream_end():
            prev_cs = None
        elif reach.get_downstream_reach() != prev_cs.reach:
            prev_cs = reach.get_downstream_reach().get_last_point(points_coll)
        for cs in reach.browse_points(points_coll):

            cs.n = manning

            if prev_cs == None:

                # downstream cs calculation
                cs.s = downstream_s
                manning_solver(cs)
                cs.v = cs.Q / (cs.width * cs.y)
                cs.h = cs.z + cs.y + cs.v ** 2 / (2 * g)
                cs.Fr = cs.v / (g * cs.y) ** 0.5
                cs.solver = "manning"
                cs.type = 0


            else:
                if prev_cs.DEM != cs.DEM:
                    cs.s = prev_cs.s
                    manning_solver(cs)
                    cs.v = cs.Q / (cs.width * cs.y)
                    cs.h = cs.z + cs.y + cs.v ** 2 / (2 * g)
                    cs.Fr = cs.v / (g * cs.y) ** 0.5
                    cs.solver = "manning"
                    cs.type = 0
                else:

                    cs_solver(cs, prev_cs)
                    cs.solver = "regular"
                    cs.type = 1

            cs.ws = cs.z + cs.y

            prev_cs = cs

    points_coll.save_points(output_pts)

    return

