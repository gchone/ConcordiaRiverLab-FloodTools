# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
# Janvier 2019
#####################################################

# v1.0 - Août 2020 - Création



import arcpy
from RunSim2DsupergcQvar_prevision_2var import *



class RunSim2D_prevision_2var(object):
    def __init__(self):

        self.label = "Lancement des simulations de prevision avec LISFLOOD-FP (2 var, une zone)"
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
            displayName="Fichier csv des débits",
            name="q",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        param_z = arcpy.Parameter(
            displayName="Fichier csv des élévations aval",
            name="z",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        param_voutput = arcpy.Parameter(
            displayName="Ouput des vitesses",
            name="voutput",
            datatype="GPBoolean",
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
        param_zbed = arcpy.Parameter(
            displayName="Élévation du lit",
            name="zbed",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_log = arcpy.Parameter(
            displayName="Fichier de log",
            name="log",
            datatype="DEFile",
            parameterType="Required",
            direction="Outpur")


        param_channelmanning.value = 0.03
        param_simtime.value = 200000
        param_voutput.value = False

        param_q.filter.list = ['csv']
        param_z.filter.list = ['csv']



        params = [param_zones, param_simfolder, param_lisflood, param_q, param_z, param_voutput, param_channelmanning, param_simtime, param_zbed, param_log]

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
        str_z = parameters[4].valueAsText
        voutput = parameters[5].valueAsText == 'true'
        channelmanning = float(parameters[6].valueAsText)
        simtime = int(parameters[7].valueAsText)
        zbed = arcpy.Raster(parameters[8].valueAsText)
        str_log = parameters[9].valueAsText

        execute_RunSim_prev_2var(str_zones, str_simfolder, str_lisflood, str_q, str_z, voutput, simtime, channelmanning, zbed, str_log, messages)

        return

