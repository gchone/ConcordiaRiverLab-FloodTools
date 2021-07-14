# -*- coding: utf-8 -*-

# Solver sous-critique uniquement

g = 9.81
#Froude_limite = 0.94
import warnings
warnings.simplefilter("ignore", RuntimeWarning)

from scipy.optimize import fsolve

def manning_solver(cs):


    def equations(y):
        R = (cs.width * y) / (cs.width + 2 * y)
        manning = (y * cs.width * R ** (2. / 3.) * cs.s ** 0.5) / cs.n - cs.Q
        return manning

    cs.y = fsolve(equations, 1)[0]
    cs.R = (cs.width * cs.y) / (cs.width + 2 * cs.y)
    cs.ycrit = (cs.Q / (cs.width * g ** 0.5)) ** (2. / 3.)

    cs.v = cs.Q / (cs.width * cs.y)
    cs.z = cs.wslidar - cs.y
    cs.h = cs.wslidar
    # with kinetic energy?
    cs.h = cs.h + cs.v ** 2 / (2 * g)
    cs.Fr = cs.v / (g * cs.y) ** 0.5


def cs_solver(cs_up, cs_down, min_slope):


    cs_tosolve = cs_down
    cs_ref = cs_up

    if cs_down.reach == cs_up.reach:
        localdist = (cs_up.dist - cs_down.dist)
    else:
        localdist = cs_down.reach.length - cs_down.dist + cs_up.dist


    if (cs_up.wslidar - cs_down.wslidar)/localdist <= min_slope:
        h_ref = cs_up.h + localdist*(min_slope - (cs_up.wslidar - cs_down.wslidar)/localdist)
    else:
        h_ref = cs_up.h
    # if (cs_up.wslidar - cs_down.wslidar)/localdist <= cs_down.s_min:
    #     h_ref = cs_up.h + localdist*(cs_down.s_min - (cs_up.wslidar - cs_down.wslidar)/localdist)
    # else:
    #     h_ref = cs_up.h

    def equations(y):

        if y < cs_tosolve.ycrit:
            # constraint simulation
            return 9999
        R = (cs_tosolve.width * y) / (cs_tosolve.width + 2 * y)
        v = cs_tosolve.Q / (cs_tosolve.width * y)
        s = (cs_tosolve.n ** 2 * v ** 2) / (R ** (4. / 3.))
        h = cs_tosolve.wslidar
        # with kinetic energy?
        h = h + v ** 2 / (2 * g)
        # slope calculation:
        #friction_h = localdist * (s+cs_ref.s)/2. # Friction can't be based on the average of slope, it leads to impossible to resolve cases
        friction_h = localdist * s
        energy = friction_h + h - h_ref
        return energy

    # premier estimé : y = y_crit
    cs_tosolve.ycrit = (cs_tosolve.Q / (cs_tosolve.width * g ** 0.5)) ** (2. / 3.)

    res, dict, ier, msg = fsolve(equations, cs_tosolve.ycrit, full_output=True)
    ## if ier != 1, an error occured.
    if ier != 1:
        cs_tosolve.y = 99
    else:
        cs_tosolve.y = res[0] # actual result of the solver

    cs_tosolve.R = (cs_tosolve.width * cs_tosolve.y) / (cs_tosolve.width + 2 * cs_tosolve.y)
    cs_tosolve.v = cs_tosolve.Q / (cs_tosolve.width * cs_tosolve.y)
    cs_tosolve.z = cs_tosolve.wslidar - cs_tosolve.y
    cs_tosolve.s = (cs_tosolve.n ** 2 * cs_tosolve.v ** 2) / (cs_tosolve.R ** (4. / 3.))
    #cs_tosolve.h = cs_tosolve.wslidar + localdist*cs_tosolve.s_min
    cs_tosolve.h = cs_tosolve.wslidar
    # with kinetic energy?
    cs_tosolve.h = cs_tosolve.h + cs_tosolve.v ** 2 / (2 * g)

    cs_tosolve.Fr = cs_tosolve.v / (g * cs_tosolve.y) ** 0.5

    return ier






