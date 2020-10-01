# -*- coding: utf-8 -*-

#####################################################
# François Larouche-Tremblay, Ing, M Sc
# Date: 24/04/2020
# Description: Interface de la fonction GenererPolygoneSurface
#####################################################

# Versions:
# v1.0 - April 2020 - François Larouche-Tremblay - Creation
# v1.1 - Sept 2020 - Guénolé Choné - Brought into the FloodTools package. Default values changed.

from RiverPolygon import *


class RiverPolygon(object):
    def __init__(self):

        self.label = "Création du polygone de surface de l'eau"
        self.description = "Génère un polygone de surface de l'eau à partir du raster des sources"
        self.canRunInBackground = True


    def getParameterInfo(self):
        param_watsurf = arcpy.Parameter(
            displayName="Raster de la surface de l'eau issu de l'algorithme de détection",
            name="watsurf",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_maxwidth = arcpy.Parameter(
            displayName="Largeur maximale des zones à remplir (en m); "
                        "Attention: Plus cette valeur est grande, plus l'algorithme risque d'inclure des portions de "
                        "berges convexes dans les secteurs de méandres ou aux confluences.",
            name="maxwidth",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_minwidth = arcpy.Parameter(
            displayName="Largeur minimale des cours d'eau d'intérêt (en m)",
            name="minwidth",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_islands = arcpy.Parameter(
            displayName="Polygone qui délimite les îles potentielles avant le traitement",
            name="islands",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param_surface = arcpy.Parameter(
            displayName="Polygone de la surface de l'eau",
            name="surface",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        param_maxwidth.value = 6
        param_minwidth.value = 3

        params = [param_watsurf, param_maxwidth, param_minwidth, param_islands, param_surface]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):

        # Récupération des paramètres
        watsurf = parameters[0].valueAsText
        maxwidth = float(parameters[1].valueAsText)
        minwidth = float(parameters[2].valueAsText)
        islands = parameters[3].valueAsText
        surface = parameters[4].valueAsText

        execute_RiverPolygon(arcpy.Raster(watsurf), maxwidth, minwidth, islands, surface, messages)

        return
