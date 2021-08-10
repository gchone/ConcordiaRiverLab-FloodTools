# -*- coding: utf-8 -*-


# Solver sous-critique uniquement

g = 9.81

import warnings
# fsolve can produce warnings. This line turns them into an Exception
warnings.simplefilter("error", RuntimeWarning)

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
    cs.h = cs.z + cs.y + cs.v ** 2 / (2 * g)
    #cs_tosolve.h = cs_tosolve.z + cs_tosolve.y
    cs.Fr = cs.v / (g * cs.y) ** 0.5


def cs_solver(cs_up, cs_down):


    cs_tosolve = cs_up
    cs_ref = cs_down

    if cs_down.reach == cs_up.reach:
        cs_up.localdist = (cs_up.dist - cs_down.dist)
    else:
        cs_up.localdist = cs_down.reach.length - cs_down.dist + cs_up.dist

    def equations(y):

        if y < cs_tosolve.ycrit:
            # constraint simulation
            return 9999
        R = (cs_tosolve.width * y) / (cs_tosolve.width + 2 * y)
        v = cs_tosolve.Q / (cs_tosolve.width * y)
        h = cs_tosolve.z + y
        # with kinetic energy?
        #h = h + (v ** 2) / (2 * g)
        s = (cs_tosolve.n ** 2 * v ** 2) / (R ** (4. / 3.))
        friction_h = cs_up.localdist * s
        #friction_h = cs_up.localdist * (s + cs_ref.s) / 2.
        energy = cs_ref.h + friction_h - h
        return energy

    # premier estimé : y = y_crit
    cs_tosolve.ycrit = (cs_tosolve.Q / (cs_tosolve.width * g ** 0.5)) ** (2. / 3.)
    cs_tosolve.y = fsolve(equations, cs_tosolve.ycrit)[0]


    cs_tosolve.R = (cs_tosolve.width * cs_tosolve.y) / (cs_tosolve.width + 2 * cs_tosolve.y)
    cs_tosolve.v = cs_tosolve.Q / (cs_tosolve.width * cs_tosolve.y)
    #cs_tosolve.h = cs_tosolve.z + cs_tosolve.y + cs_tosolve.v ** 2 / (2 * g)
    cs_tosolve.h = cs_tosolve.z + cs_tosolve.y
    cs_tosolve.s = (cs_tosolve.n ** 2 * cs_tosolve.v ** 2) / (cs_tosolve.R ** (4. / 3.))
    cs_tosolve.Fr = cs_tosolve.v / (g * cs_tosolve.y) ** 0.5


    del cs_up.localdist

