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


def execute_Simple1Dhydraulic(rivernet, points_coll, manning, downstream_s, messages):
    # Compute water level
    # require three attributes in the points collection points_coll: "z" (bed elevation), "Q", "width"
    # create a new attribute: "ws"


    for reach in rivernet.browse_reaches_down_to_up():
        # Looking for the upstream datapoint
        if reach.is_upstream_end():
            prev_cs = None

        for cs in reach.browse_points(collection=points_coll):

            cs.n = manning

            if prev_cs == None:

                # downstream cs calculation
                cs.s = downstream_s
                manning_solver(cs)

                cs.solver = "manning"
                cs.type = 0


            else:

                cs_solver(cs, prev_cs)

            cs.ws = cs.z + cs.y

            prev_cs = cs


    return





