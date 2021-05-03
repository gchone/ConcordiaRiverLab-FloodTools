# -*- coding: utf-8 -*-

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################


import os
import arcpy

from SolverLisflood import *


def execute_Simple1Dhydraulic(rivernet, points_coll, manning, downstream_s, messages):
    # Compute water level
    # require three attributes in the points collection points_coll: "z" (bed elevation), "Q", "width"
    # create a new attribute: "ws"


    for reach in rivernet.browse_reaches(orientation="UP_TO_DOWN"):
        # Looking for the upstream datapoint
        if reach.is_upstream_end():
            prev_cs = None

        for cs in reach.browse_points(points_collection=points_coll):

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

                cs_solver(cs, prev_cs)

            cs.ws = cs.z + cs.y

            prev_cs = cs


    return





