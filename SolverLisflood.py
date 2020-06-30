# coding: latin-1



# Solver sous-critique uniquement

g = 9.81
#Froude_limite = 0.94
import warnings
warnings.simplefilter("error", RuntimeWarning)
import tree.ProfilePoint

def manning_solver(cs):
    # peut-être optimisé
    # fonctionnement actuel:
    # - sous-estime Q en calculant y sans frottements latéraux
    # - incrémente y au décimètre jusqu'à avoir un Q supérieur à la cible
    # - décrémente y au centimètre jusqu'à avoir un Q inférieur à la cible
    # - incrémente y au millimètre jusqu'à avoir un Q supérieur à la cible
    slope = cs.s
    y = (cs.Q*cs.n/(cs.width*slope**0.5))**(3./5.)
    increment = 0.1
    Qcalc = 0
    while Qcalc<cs.Q:
        y = y + increment
        R = (cs.width*y)/(cs.width+2*y)
        Qcalc = (y*cs.width*R**(2./3.)*slope**0.5)/cs.n
    increment = 0.01
    while Qcalc >= cs.Q:
        y = y - increment
        R = (cs.width * y) / (cs.width + 2 * y)

        Qcalc = (y * cs.width * R ** (2. / 3.) * slope ** 0.5) / cs.n

    increment = 0.001
    while Qcalc < cs.Q:
        y = y + increment
        R = (cs.width * y) / (cs.width + 2 * y)
        Qcalc = (y * cs.width * R ** (2. / 3.) * slope ** 0.5) / cs.n
    cs.y = y
    cs.R = R



def cs_solver(cs_up, cs_down):


    cs_tosolve = cs_up
    cs_ref = cs_down



    # premier estimé : y = y_crit

    cs_tosolve.y = (cs_tosolve.Q / (cs_tosolve.width * g ** 0.5)) ** (2. / 3.)
    increment = 0
    stoploop = False

    while not stoploop:
        cs_tosolve.y += increment

        cs_tosolve.R = (cs_tosolve.width * cs_tosolve.y) / (cs_tosolve.width + 2 * cs_tosolve.y)

        cs_tosolve.v = cs_tosolve.Q / (cs_tosolve.width * cs_tosolve.y)
        #cs_tosolve.h = cs_tosolve.zlidar + cs_tosolve.y + cs_tosolve.v ** 2 / (2 * g)
        cs_tosolve.h = cs_tosolve.zlidar + cs_tosolve.y
        cs_tosolve.s = (cs_tosolve.n ** 2 * cs_tosolve.v ** 2) / (cs_tosolve.R ** (4. / 3.))
        cs_tosolve.Fr = cs_tosolve.v / (g * cs_tosolve.y) ** 0.5


        #friction_h = cs_up.dist * (cs_tosolve.s + cs_ref.s) / 2.
        Kref = (1./cs_ref.n)*cs_ref.width*cs_ref.y*(cs_ref.R ** (2. / 3.))
        Ktosolve = (1./cs_tosolve.n)*cs_tosolve.width*cs_tosolve.y*(cs_tosolve.R ** (2. / 3.))

        #friction_h = cs_up.dist * ((cs_tosolve.Q + cs_ref.Q)/(Kref+Ktosolve))**2
        friction_h = cs_up.dist * cs_tosolve.s

        if increment == -0.001 and cs_tosolve.h < cs_ref.h + friction_h :
            stoploop = True
            cs_tosolve.y -= increment

            cs_tosolve.type = 1
        if increment == -0.001 and cs_tosolve.y < cs_ref.zlidar+cs_ref.y-cs_tosolve.zlidar:
            stoploop = True
            cs_tosolve.y = cs_ref.zlidar+cs_ref.y-cs_tosolve.zlidar

            cs_tosolve.type = 2
        if increment == 0.01 and cs_tosolve.h > cs_ref.h + friction_h:
            increment = -0.001



        if increment == 0 :
            if cs_tosolve.h > cs_ref.h + friction_h:
                stoploop = True
                cs_tosolve.type = 3


            else:
                increment = 0.01





    cs_tosolve.R = (cs_tosolve.width * cs_tosolve.y) / (cs_tosolve.width + 2 * cs_tosolve.y)
    cs_tosolve.v = cs_tosolve.Q / (cs_tosolve.width * cs_tosolve.y)
    #cs_tosolve.h = cs_tosolve.zlidar + cs_tosolve.y + cs_tosolve.v ** 2 / (2 * g)
    cs_tosolve.h = cs_tosolve.zlidar + cs_tosolve.y
    cs_tosolve.s = (cs_tosolve.n ** 2 * cs_tosolve.v ** 2) / (cs_tosolve.R ** (4. / 3.))
    cs_tosolve.Fr = cs_tosolve.v / (g * cs_tosolve.y) ** 0.5



