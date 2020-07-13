# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
# Janvier 2019
#####################################################

# v1.1 - octobre 2019 - version 1.0 modifiée pour simulations de l'amont vers l,aval avec reprise de l'élévation aval comme condition limite:
# v1.2 - octobre 2019 - stabilisation des simulations
# v1.3 - feb 2020 - Utilisation des résultats en fin de simulation si le steady state n'est pas atteint
# v1.4 - Mai 2020 - Separation interface


import arcpy
from RunSim2DsupergcQvar_hdown import *



class RunSim2DsupergcQvar_hdown(object):
    def __init__(self):

        self.label = "Lancement des simulations avec LISFLOOD-FP"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):



        param_zones = arcpy.Parameter(
            displayName="Dossier des zones",
            name="zones",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param_simfolder = arcpy.Parameter(
            displayName="Dossier des simulations",
            name="sim",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param_lisflood = arcpy.Parameter(
            displayName="Dossier du programme LISFLOOD-FP",
            name="lisflood",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param_q = arcpy.Parameter(
            displayName="Raster des débits",
            name="q",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_voutput = arcpy.Parameter(
            displayName="Ouput des vitesses",
            name="voutput",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param_lakes = arcpy.Parameter(
            displayName="Polygones des extrémités aval (lacs)",
            name="lakes",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_zfield = arcpy.Parameter(
            displayName="Field for boundary condition",
            name="z_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_channelmanning = arcpy.Parameter(
            displayName="Coefficient de Manning dans le chenal",
            name="channelmanning",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param_simtime = arcpy.Parameter(
            displayName="Temps de simulation maximum (s)",
            name="simtime",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")


        param_channelmanning.value = 0.03
        param_simtime.value = 200000
        param_voutput.value = False
        param_lakes.filter.list = ["Polygon"]
        param_zfield.parameterDependencies = [param_lakes.name]


        params = [param_zones, param_simfolder, param_lisflood, param_q, param_voutput, param_lakes, param_zfield, param_channelmanning, param_simtime]

        return params

    def isLicensed(self):

        return True

    def updateParameters(self, parameters):

        return

    def updateMessages(self, parameters):

        return

    def execute(self, parameters, messages):

        # Récupération des paramètres

        str_zones = parameters[0].valueAsText
        str_simfolder = parameters[1].valueAsText
        str_lisflood = parameters[2].valueAsText
        str_q = parameters[3].valueAsText
        voutput = bool(parameters[4].valueAsText)
        str_lakes = parameters[5].valueAsText
        zfield = parameters[6].valueAsText
        channelmanning = float(parameters[7].valueAsText)
        simtime = int(parameters[8].valueAsText)

        execute_RunSim(str_zones, str_simfolder, str_lisflood, arcpy.Raster(str_q), str_lakes, zfield, voutput, simtime, channelmanning, messages)

        return

