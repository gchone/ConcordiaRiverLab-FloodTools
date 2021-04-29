# coding: latin-1

# v0.2 Nov 2020. Clarification du nom des variables
# v0.21 Nov 2020. Avec un vrai solver

# Solver sous-critique uniquement

g = 9.81
#Froude_limite = 0.94
import warnings
warnings.simplefilter("error", RuntimeWarning)
import tree.ProfilePoint
from scipy.optimize import fsolve

def manning_solver(cs):

    try:
        def equations(y):
            R = (cs.width * y) / (cs.width + 2 * y)
            manning = (y * cs.width * R ** (2. / 3.) * cs.s ** 0.5) / cs.n - cs.Q
            return manning

        cs.y = fsolve(equations, 1)[0]
        v = cs.Q / (cs.width * cs.y)
        cs.h = cs.z + cs.y + v ** 2 / (2 * g)
        #cs.R = (cs.width * cs.y) / (cs.width + 2 * cs.y)
    except RuntimeWarning as e:
        print (cs.wslidar)
        print (cs.width)
        print (cs.Q)
        print (e)
        raise e


def cs_solver(cs_up, cs_down):


    cs_tosolve = cs_up
    cs_ref = cs_down

    def equations(y):

        if y < ycrit:
            # constraint simulation
            return 9999
        R = (cs_tosolve.width * y) / (cs_tosolve.width + 2 * y)
        v = cs_tosolve.Q / (cs_tosolve.width * y)
        h = cs_tosolve.z + y
        s = (cs_tosolve.n ** 2 * v ** 2) / (R ** (4. / 3.))
        friction_h = cs_up.dist * s
        energy = cs_ref.h + friction_h - h
        return energy

    try:
        # premier estimé : y = y_crit
        ycrit = (cs_tosolve.Q / (cs_tosolve.width * g ** 0.5)) ** (2. / 3.)
        cs_tosolve.y = fsolve(equations, ycrit)[0]
    except RuntimeWarning as e:
        print (cs_tosolve.wslidar)
        print (cs_tosolve.width)
        print (cs_tosolve.Q)
        print (e)
        raise e

    R = (cs_tosolve.width * cs_tosolve.y) / (cs_tosolve.width + 2 * cs_tosolve.y)
    v = cs_tosolve.Q / (cs_tosolve.width * cs_tosolve.y)
    #cs_tosolve.h = cs_tosolve.z + cs_tosolve.y + cs_tosolve.v ** 2 / (2 * g)
    cs_tosolve.h = cs_tosolve.z + cs_tosolve.y
    cs_tosolve.s = (cs_tosolve.n ** 2 * v ** 2) / (R ** (4. / 3.))
    #cs_tosolve.Fr = cs_tosolve.v / (g * cs_tosolve.y) ** 0.5



