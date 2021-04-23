# coding: latin-1

# Solver sous-critique uniquement

g = 9.81
#Froude_limite = 0.94
import warnings
warnings.simplefilter("error", RuntimeWarning)

from scipy.optimize import fsolve

def manning_solver(cs):


    def equations(y):
        R = (cs.width * y) / (cs.width + 2 * y)
        manning = (y * cs.width * R ** (2. / 3.) * cs.s ** 0.5) / cs.n - cs.Q
        return manning

    cs.y = fsolve(equations, 1)[0]
    cs.R = (cs.width * cs.y) / (cs.width + 2 * cs.y)



def cs_solver(cs_up, cs_down):


    cs_tosolve = cs_down
    cs_ref = cs_up

    def equations(y):

        if y < cs_tosolve.ycrit:
            # constraint simulation
            return 9999
        R = (cs_tosolve.width * y) / (cs_tosolve.width + 2 * y)
        v = cs_tosolve.Q / (cs_tosolve.width * y)
        s = (cs_tosolve.n ** 2 * v ** 2) / (R ** (4. / 3.))
        z = cs_tosolve.wslidar - y
        h = cs_tosolve.wslidar
        # with kinetic energy?
        h = h + v ** 2 / (2 * g)
        # slope calculation:
        #friction_h = (cs_up.dist - cs_down.dist) * s
        friction_h = (cs_up.dist - cs_down.dist) * (s+cs_ref.s)/2.
        energy = h + friction_h - cs_up.h
        return energy

    # premier estim� : y = y_crit
    cs_tosolve.ycrit = (cs_tosolve.Q / (cs_tosolve.width * g ** 0.5)) ** (2. / 3.)
    cs_tosolve.y = fsolve(equations, cs_tosolve.ycrit)[0]

    cs_tosolve.R = (cs_tosolve.width * cs_tosolve.y) / (cs_tosolve.width + 2 * cs_tosolve.y)
    cs_tosolve.v = cs_tosolve.Q / (cs_tosolve.width * cs_tosolve.y)
    cs_tosolve.z = cs_tosolve.wslidar - cs_tosolve.y
    cs_tosolve.h = cs_tosolve.wslidar
    # with kinetic energy?
    cs_tosolve.h = cs_tosolve.h + cs_tosolve.v ** 2 / (2 * g)
    cs_tosolve.s = (cs_tosolve.n ** 2 * cs_tosolve.v ** 2) / (cs_tosolve.R ** (4. / 3.))
    cs_tosolve.Fr = cs_tosolve.v / (g * cs_tosolve.y) ** 0.5



