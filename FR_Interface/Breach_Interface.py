# coding: latin-1

#####################################################
# Gu�nol� Chon�
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Mars 2017 - Cr�ation
# v1.1 - Juin 2018 - S�paration de l'interface et du m�tier
# v1.2 - D�cembre 2018 - Ajout du workspace

import arcpy
from Breach import *


class Breach(object):
    def __init__(self):

        self.label = "Br�chage"
        self.description = "Supprime les remont�es en suivant l'�coulement"
        self.canRunInBackground = False


    def getParameterInfo(self):

        param_elevation = arcpy.Parameter(
            displayName="Ligne d'�l�vations � corriger",
            name="elevationligne",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_flowdir = arcpy.Parameter(
            displayName="Flow direction",
            name="flowdir",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_frompoint = arcpy.Parameter(
            displayName="Points de d�part",
            name="frompoint",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_breached = arcpy.Parameter(
            displayName="�l�vations corrig�es",
            name="flowbreached",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")
        param0 = arcpy.Parameter(
            displayName="Workspace",
            name="in_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param0.filter.list = ["File System"]
        param0.value = arcpy.env.scratchWorkspace
        param_frompoint.filter.list = ["Point"]

        params = [param_elevation, param_flowdir, param_frompoint, param_breached, param0]

        return params

    def isLicensed(self):

        return True

    def updateParameters(self, parameters):

        return

    def updateMessages(self, parameters):

        return

    def execute(self, parameters, messages):

        # R�cup�ration des param�tres
        str_dem = parameters[0].valueAsText
        str_flowdir = parameters[1].valueAsText
        str_frompoint = parameters[2].valueAsText

        SaveResult = parameters[3].valueAsText

        arcpy.env.scratchWorkspace =  parameters[4].valueAsText

        execute_Breach(arcpy.Raster(str_dem), arcpy.Raster(str_flowdir), str_frompoint, SaveResult, messages)

        return