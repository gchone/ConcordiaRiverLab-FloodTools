# -*- coding: utf-8 -*-

#####################################################
# François Lrouche-Tremblay, Ing, M Sc
# Description:
#####################################################

# Version 3 mai 2021

# Toolbox permettant d'utiliser l'outil de calcul de largeur des cours d'eau par transects

from LargeurParTransect_Interface import *

class Toolbox(object):
    def __init__(self):

        self.label = "Toolbox Largeur Par Transects"
        self.alias = "lpt"


        self.tools = [LargeurParTransect]
