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
#from Solver2 import *
from SolverLisflood import *


def execute_BedAssessment(rivernet, points_coll, manning, downstream_s, messages):
    # Compute the bed assessment
    # require three attributes in the points collection points_coll: "wslidar", "Q", "width"
    # create a new attribute: "z"



    enditeration = False
    iteration = 0
    while not enditeration:
        iteration += 1

        # 1D hydraulic calculations
        for reach in rivernet.browse_reaches():
            # Looking for the downstream datapoint
            if reach.is_downstream_end():
                prev_cs = None
            else:
                prev_cs = reach.get_downstream_reach().get_last_point(points_coll)

            for cs in reach.browse_points(points_collection=points_coll):
                cs.n = manning
                if iteration == 1:
                    cs.z = cs.wslidar
                    cs.ws = cs.wslidar

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


                cs.prev_ws = cs.ws
                cs.ws = cs.z + cs.y
                cs.dif = cs.ws - cs.wslidar


                prev_cs = cs




        corrections = []
        # down to up
        for reach in rivernet.browse_reaches():
            # Looking for the downstream datapoint
            if reach.is_downstream_end():
                prev_cs = None
            else:
                prev_cs = reach.get_downstream_reach().get_last_point(points_coll)

            for cs in reach.browse_points(points_collection=points_coll):
                if prev_cs != None:
                    if prev_cs.z_fill > cs.z:
                        if prev_cs.z == prev_cs.z_fill:
                            # first backwater cell
                            correction = []
                            corrections.append(correction)
                            cs.idcorrection = len(corrections) - 1
                        else:
                            correction = corrections[prev_cs.idcorrection]
                            cs.idcorrection = prev_cs.idcorrection
                        cs.z_fill = prev_cs.z_fill
                        correction.append(cs)
                    else:
                        cs.z_fill = cs.z
                        correction = []
                        correction.append(cs)
                        corrections.append(correction)
                        cs.idcorrection = len(corrections) - 1
                else:
                    cs.z_fill = cs.z
                    correction = []
                    correction.append(cs)
                    corrections.append(correction)
                    cs.idcorrection = len(corrections) - 1

                prev_cs = cs

        enditeration = True
        for correction in corrections:
            sumdif = 0
            sumdifws = 0
            for cscorrect in correction:
                sumdif += cscorrect.dif
                sumdifws += cscorrect.ws - cscorrect.prev_ws
            correcteddif = sumdif / len(correction)
            difws = abs(sumdifws) / len(correction)
            if difws > 0.01:
                for cscorrect in correction:
                    cscorrect.z = cscorrect.z - correcteddif
                enditeration = False

    return



