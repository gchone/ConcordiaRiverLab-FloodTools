# coding: latin-1

##################################################################
# Auteur: François Larouche-Tremblay, Ing, M Sc
# Date: 20/09/2019
# Description: Interface de la fonction "ChanelDetection"
##################################################################

# Versions:
# v1.0 - Sept 2019 - François Larouche-Tremblay - Creation
# v1.1 - May 2020 - Guénolé Choné - Brought into the FloodTools package

from ChanelDetection import *
import arcpy

class ChanelDetection(object):
    def __init__(self):

        self.label = "Détection de l'étendue des sources"
        self.description = "Identifie les cours d'eau de manière itérative"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param_streams = arcpy.Parameter(
            displayName="Élévations du chenal ou du HAND zéro",
            name="streams",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_dem = arcpy.Parameter(
            displayName="MNE du bassin versant",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_niter = arcpy.Parameter(
            displayName="Nombre maximal d'itérations de l'algorithme",
            name="niter",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_globaltol = arcpy.Parameter(
            displayName="Différence de hauteur maximale tolérée",
            name="global",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_offlim = arcpy.Parameter(
            displayName="Raster des zones exclues de l'analyse",
            name="offlim",
            datatype="GPRasterLayer",
            parameterType="Optional",
            direction="Input")
        param_brch = arcpy.Parameter(
            displayName="Lignes des chenaux",
            name="polybed",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Input")
        param_postpro = arcpy.Parameter(
            displayName="Post-traitement des sources (remplissage des orphelins et surfaces rugeuses)",
            name="postpro",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param_checkelev = arcpy.Parameter(
            displayName="Post-validation des élévations",
            name="checkelev",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param_eltol = arcpy.Parameter(
            displayName="Différence de hauteur maximale tolérée entre un orphelin et ses voisins",
            name="eltol",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_watsurf = arcpy.Parameter(
            displayName="Raster de la surface de l'eau",
            name="watsurf",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")

        param_niter.value = 20
        param_globaltol.value = 0.5
        param_brch.filter.list = ["Polyline"]


        params = [param_streams, param_dem, param_niter, param_globaltol, param_offlim, param_brch, param_postpro, param_checkelev, param_eltol, param_watsurf]

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if parameters[7].valueAsText == 'true':
            parameters[8].enabled = True
            parameters[8].value = 0.5
        else:
            parameters[8].enabled = False


        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):


        # Récupération des paramètres
        streams = arcpy.Raster(parameters[0].valueAsText)
        dem = arcpy.Raster(parameters[1].valueAsText)
        niter = int(parameters[2].valueAsText)
        globaltol = float(parameters[3].valueAsText)
        offlim = parameters[4].valueAsText
        if offlim and offlim != "#":
            offlim = arcpy.Raster(parameters[4].valueAsText)

        brch = parameters[5].valueAsText
        postpro = bool(parameters[6].valueAsText)
        checkelev = bool(parameters[7].valueAsText)
        if checkelev:
            localtol = float(parameters[8].valueAsText)
        else:
            localtol = None
        watsurf = parameters[9].valueAsText

        execute_ChanelDetection(streams, dem, niter, offlim, brch, postpro,  checkelev, localtol, globaltol, watsurf,
                                messages)


        return
