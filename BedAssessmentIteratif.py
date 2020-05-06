# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Mai 2019 - Création


import os
import arcpy
import pickle
from RasterIO import *
from tree.OurTreeSegment import *
from tree.OurTreeManager import *
#from Solver2 import *
from SolverLisflood import *


def execute_BedAssessment(r_flowdird4, str_frompoint, r_width, r_zwater, r_manning, result, r_Q, messages, picklefile = None):




    if picklefile is not None and os.path.exists(picklefile):
        pickletree = open(picklefile, 'rb')
        tree = pickle.load(pickletree)
    else:
        flowdir = RasterIO(r_flowdird4)
        zwater = RasterIO(r_zwater)
        width = RasterIO(r_width)
        Q = RasterIO(r_Q)
        manning = RasterIO(r_manning)
        # manning = r_manning
        tree = OurTreeManager()
        tree.build_tree(flowdir,str_frompoint,width=width,wslidar=zwater,n=manning,Q=Q)
        if picklefile is not None:
            pickletree = open(picklefile, 'wb')
            pickle.dump(tree, pickletree)
            pickletree.close()

    print "arbre construit"
    print tree.treeroot

    Result = RasterIO(r_flowdird4, result, float, -255)


    # A paramétrer
    downstream_s = 0.0001
    #downstream_s = 0.004

    enditeration = False
    iteration = 0
    while not enditeration:
        iteration += 1
        print iteration


        # 1D hydraulic calculations
        prevsegid = 0
        for segment, prev_cs, cs in tree.browsepts():
            #cs.n = manning
            if iteration == 1:
                cs.zlidar = cs.wslidar
                cs.ws = cs.wslidar

            if prev_cs == None:

                # downstream cs calculation
                cs.s = downstream_s
                manning_solver(cs)
                cs.v = cs.Q / (cs.width * cs.y)
                cs.h = cs.zlidar + cs.y + cs.v ** 2 / (2 * g)
                cs.Fr = cs.v / (g * cs.y) ** 0.5
                cs.solver = "manning"
                cs.type = 0


            else:
                # if prevsegid <> segment.id:
                #     print segment.id
                cs_solver(cs, prev_cs)
                #print str(cs.zlidar)+ ", " + str(cs.col) +  ", " + str(cs.row)+  ", " + str(cs.dist)

            cs.prev_ws = cs.ws
            cs.ws = cs.zlidar + cs.y
            cs.dif = cs.ws - cs.wslidar


            prevsegid = segment.id




        corrections = []
        # down to up
        for segment, prev_cs, cs in tree.browsepts():
            if prev_cs != None:
                if prev_cs.z_fill > cs.zlidar:
                    if prev_cs.zlidar == prev_cs.z_fill:
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
                    cs.z_fill = cs.zlidar
                    correction = []
                    correction.append(cs)
                    corrections.append(correction)
                    cs.idcorrection = len(corrections) - 1
            else:
                cs.z_fill = cs.zlidar
                correction = []
                correction.append(cs)
                corrections.append(correction)
                cs.idcorrection = len(corrections) - 1

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
                    cscorrect.zlidar = cscorrect.zlidar - correcteddif
                enditeration = False


    print "Done: saving"
    for segment in tree.treesegments():
        for pt in segment.get_profile():
            Result.setValue(pt.row, pt.col, pt.zlidar)
            #Result.setValue(pt.row, pt.col, pt.Fr)

    Result.save()


    return



