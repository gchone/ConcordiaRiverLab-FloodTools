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
    # Compute the bed assessment
    # require three attributes in the points collection points_coll: "wslidar", "Q", "width"
    # create a new attribute: "z"

    # TODO:
    # upstream_s : prendre la pente de la surface avec le point downstream.
    # when passing a second time on a downstream reach, stop if the bed calculated is close to the previously calculated one

    # 1D hydraulic calculations
    for reach in rivernet.browse_reaches(orientation="UP_TO_DOWN"):
        # Looking for the upstream datapoint
        if reach.is_upstream_end():
            prev_cs = None
        # no else: if it's not an upstream reach the prev_cs is already good

        for cs in reach.browse_points(points_collection=points_coll, orientation="UP_TO_DOWN"):
            cs.n = manning


            if prev_cs == None:

                # downstream cs calculation
                cs.s = upstream_s
                manning_solver(cs)
                cs.z = cs.wslidar - cs.y
                cs.v = cs.Q / (cs.width * cs.y)
                cs.h = cs.z + cs.y + cs.v ** 2 / (2 * g)
                cs.Fr = cs.v / (g * cs.y) ** 0.5
                cs.solver = "manning"
                cs.type = 0


            else:

                if cs.wslidar < prev_cs.wslidar:
                    __recursive_inverse1Dhydro(cs, prev_cs)

                else:
                    cs.z = -9999
                    cs.v = 0
                    cs.h = cs.wslidar
                    cs.Fr = 0
                    cs.solver = "infinite"
                    cs.type = 2
                    cs.s = 0

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
            newcs = cs.reach.add_point(newdist, 0, cs.collectionname)
            # TODO:
            # Temporary. Certainly not the cleanest way to proceed
            a = (cs.width - prev_cs.width) / (cs.dist - prev_cs.dist)
            newcs.width = a * newcs.dist + cs.width - a * cs.dist
            a = (cs.Q - prev_cs.Q) / (cs.dist - prev_cs.dist)
            newcs.Q = a * newcs.dist + cs.Q - a * cs.dist
            a = (cs.wslidar - prev_cs.wslidar) / (cs.dist - prev_cs.dist)
            newcs.wslidar = a* newcs.dist + cs.wslidar - a* cs.dist
            newcs.n = cs.n

            __recursive_inverse1Dhydro(newcs, prev_cs)
            newcs.solver = "added"
            cs.type = 3
            __recursive_inverse1Dhydro(cs, newcs)

        else:
            # TODO:
            # case where the interpolation takes place between two reaches
            pass

