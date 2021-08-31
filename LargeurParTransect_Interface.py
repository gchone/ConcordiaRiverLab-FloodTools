# -*- coding: utf-8 -*-

#####################################################
# Auteur: François Larouche-Tremblay, Ing, M Sc
# Date: 04/05/2021
# Description: Interface de la fonction LargeurParTransect
#####################################################

import arcpy
from WidthAssessment import *


class LargeurParTransect(object):
    def __init__(self):
        self.label = "Largeur par transects"
        self.description = "Génère un profil de points contenant la largeur des cours d'eau calculée " \
                           "à partir de transects ainsi que les transects associés à chaque point."
        self.canRunInBackground = True

    def getParameterInfo(self):
        param_streamnetwork = arcpy.Parameter(
            displayName="Réseau vectoriel de l'écoulement",
            name="streamnetwork",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_idfield = arcpy.Parameter(
            displayName="Nom du champ qui contient l'ID du tronçon (Nombre entier)",
            name="idfield",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param_riverbed = arcpy.Parameter(
            displayName="Polygone de la surface des cours d'eau",
            name="riverbed",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_ineffarea = arcpy.Parameter(
            displayName="Polygones recouvrant les branches de cours d'eau "
                        "ineffectives (trop petites, secondaires, intermittentes)",
            name="ineffarea",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param_maxwidth = arcpy.Parameter(
            displayName="Largeur maximale des transects (en m)",
            name="maxwidth",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_spacing = arcpy.Parameter(
            displayName="Espacement régulier entre les sections transversales (en m)",
            name="spacing",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_transects = arcpy.Parameter(
            displayName="Transects sur la ligne centrale contenant les données d'élévation",
            name="transects",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")
        param_cspoints = arcpy.Parameter(
            displayName="Points aux sections d'écoulement qui contiendront les données de modélisation",
            name="outpts",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output")

        param_streamnetwork.filter.list = ["Polyline"]
        param_idfield.enabled = False
        param_riverbed.filter.list = ["Polygon"]
        param_ineffarea.filter.list = ["Polygon"]
        param_maxwidth.value = 200
        param_spacing.value = 8

        params = [param_streamnetwork, param_idfield, param_riverbed, param_ineffarea, param_maxwidth,
                  param_spacing, param_transects, param_cspoints]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if parameters[0].valueAsText:  # streamnetwork a été spécifié
            parameters[1].enabled = True
            parameters[1].filter.list = [f.name for f in arcpy.ListFields(parameters[0].valueAsText)]
        else:
            parameters[1].enabled = False

        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # Récupération des paramètres

        streamnetwork = parameters[0].valueAsText
        idfield = parameters[1].valueAsText
        riverbed = parameters[2].valueAsText
        ineffarea = parameters[3].valueAsText
        maxwidth = int(parameters[4].valueAsText)
        spacing = float(parameters[5].valueAsText)
        transects = parameters[6].valueAsText
        cspoints = parameters[7].valueAsText

        execute_largeurpartransect(streamnetwork, idfield, riverbed, ineffarea, maxwidth, spacing,
                                   transects, cspoints, messages)

        return
