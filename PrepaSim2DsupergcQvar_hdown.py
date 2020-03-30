# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
# Janvier 2019
#####################################################

# v1.2 - octobre 2019 - version 1.0 modifiée pour simulations de l'amont vers l,aval avec reprise de l'élévation aval comme condition limite:
#   suppression des infos sur les conditions limites aval
# v1.3 - octobre 2019 - stabilisation des simulations:
#   * HFIX transformé en HVAR

import os
import arcpy
import subprocess
from RasterIO import *



class PrepaSim2DsupergcQvar_hdown(object):
    def __init__(self):

        self.label = "Prepa SuperGC H_DOWN"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):



        param_zones = arcpy.Parameter(
            displayName="Dossier des zones",
            name="zones",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        param_width = arcpy.Parameter(
            displayName="Largeur",
            name="width",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_zbed = arcpy.Parameter(
            displayName="Élévation du lit",
            name="zbed",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_manning = arcpy.Parameter(
            displayName="Manning en plaine",
            name="manning",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_mask = arcpy.Parameter(
            displayName="Masque du chenal",
            name="mask",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param_channelmanning = arcpy.Parameter(
            displayName="Coefficient de Manning dans le chenal",
            name="channelmanning",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param_output = arcpy.Parameter(
            displayName="Dossier de sortie",
            name="folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")




        params = [param_zones, param_width, param_zbed, param_manning, param_mask, param_channelmanning, param_output]

        return params

    def isLicensed(self):

        return True

    def updateParameters(self, parameters):

        return

    def updateMessages(self, parameters):

        return

    def execute(self, parameters, messages):

        # Temps de simulation
        simtime = 200000

        # Récupération des paramètres
        str_zones = parameters[0].valueAsText
        str_width = parameters[1].valueAsText
        str_zbed =parameters[2].valueAsText
        str_manning =parameters[3].valueAsText
        str_mask = parameters[4].valueAsText
        channelmanning = float(parameters[5].valueAsText)
        str_output = parameters[6].valueAsText

        r_width = arcpy.Raster(str_width)

        str_inbci = str_zones + "\\inbci.shp"
        str_outbci = str_zones + "\\outbci.shp"

        # Création des dossiers de sortie s'ils n'existent pas
        if not os.path.isdir(str_output):
            os.makedirs(str_output)
        if not os.path.isdir(str_output + "\\lisflood\\"):
            os.makedirs(str_output + "\\lisflood\\")



        # Création des fichiers .bci à partir des information du fichier inbci.shp
        # count est utilisé pour compter le nombre de zones, pour la barre de progression lors des simulations
        count = 0

        bcipointcursor = arcpy.da.SearchCursor(str_inbci, ["SHAPE@", "zone", "discharge", "type"])
        dictsegmentsin = {}
        for point in bcipointcursor:
            if not os.path.exists(str_output + "\\mxe_" + point[1]):
                if point[1] not in dictsegmentsin:
                    dictsegmentsin[point[1]] = []
                dictsegmentsin[point[1]].append(point)



        for segment in dictsegmentsin.values():
            for point in sorted(segment, key=lambda q: q[2]):
                if point[3]=="main":
                    count += 1
                    latnum = 0

                    pointshape = point[0].firstPoint

                    # Calcul du débit
                    pointdischarge = point[2]/((r_width.meanCellHeight+r_width.meanCellWidth)/2)
                    lastdischarge = point[2]



                    # Création du fichier
                    newfile = str_output + "\\lisflood\\" + point[1] + "prepa.bci"

                    # Enregistrement des coordonnées et du débit pour le point source
                    filebci = open(newfile, 'w')
                    filebci.write("P\t" + str(int(pointshape.X)) + "\t" + str(int(pointshape.Y)) + "\tQVAR\t" + point[1] + "\n")
                    filebci.close()

                    # Création du fichier bdy
                    newfilebdy = str_output + "\\lisflood\\" + point[1] + "prepa.bdy"
                    filebdy = open(newfilebdy, 'w')
                    filebdy.write(point[1] + ".bdy\n")
                    filebdy.write(point[1] + "\n")
                    filebdy.write("3\tseconds\n")
                    filebdy.write("0\t0\n")
                    filebdy.write("{0:.3f}".format(pointdischarge) + "\t50000\n")
                    filebdy.write("{0:.3f}".format(pointdischarge) + "\t" + str(simtime))
                    filebdy.close()

                if point[3] == "lateral":
                    pointshape = point[0].firstPoint
                    # Calcul du débit
                    pointdischarge = (point[2]-lastdischarge)/ ((r_width.meanCellHeight + r_width.meanCellWidth) / 2)
                    lastdischarge = point[2]

                    latnum +=1
                    newfile = str_output + "\\lisflood\\" + point[1] + "prepa.bci"

                    # Enregistrement des coordonnées et du débit pour le point source
                    filebci = open(newfile, 'a')
                    filebci.write(
                        "P\t" + str(int(pointshape.X)) + "\t" + str(int(pointshape.Y)) + "\tQVAR\t" + point[1]+"_"+str(latnum) + "\n")
                    filebci.close()

                    # fichier bdy
                    newfilebdy = str_output + "\\lisflood\\" + point[1] + "prepa.bdy"
                    filebdy = open(newfilebdy, 'a')
                    filebdy.write("\n" + point[1]+"_"+str(latnum) + "\n")
                    filebdy.write("3\tseconds\n")
                    filebdy.write("0\t0\n")
                    filebdy.write("{0:.3f}".format(pointdischarge) + "\t50000\n")
                    filebdy.write("{0:.3f}".format(pointdischarge) + "\t" + str(simtime))
                    filebdy.close()






        # Création des fichiers .par et conversion des rasters en fichiers ASCII (un par point source comme il n'y a qu'un seul point d'entrée par simulation)

        for segment in dictsegmentsin.values():
            for point in sorted(segment, key=lambda q: q[2]):

                if point[3]=="main":

                    newfile = str_output + "\\lisflood\\" + point[1] + ".par"
                    filepar = open(newfile, 'w')
                    filepar.write("DEMfile\t" + point[1] + ".txt\n")
                    filepar.write("resroot\t" + point[1] + "\n")
                    filepar.write("dirroot\t" + "res\n")
                    filepar.write("manningfile\tn" + point[1] + ".txt\n")
                    filepar.write("bcifile\t" + point[1] +".bci" + "\n")
                    filepar.write("sim_time\t" + str(simtime) + "\n")
                    filepar.write("saveint\t" + str(simtime) + "\n")
                    filepar.write("bdyfile\t" + point[1] + ".bdy" + "\n")
                    filepar.write("SGCwidth\tw" + point[1] + ".txt\n")
                    filepar.write("SGCbank\t" + point[1] + ".txt\n")
                    filepar.write("SGCbed\td" + point[1] + ".txt\n")
                    filepar.write("SGCn\t" + str(channelmanning) + "\n")
                    filepar.write("chanmask\tm" + point[1] + ".txt\n")


                    # On peut ajouter la ligne suivante si on souhaite avoir les vitesses du courant
                    #filepar.write("hazard\n")
                    filepar.write("cfl\t0.5\n")
                    filepar.write("max_Froude\t1\n")
                    #filepar.write("debug\n")
                    filepar.close()

                    arcpy.Clip_management(str_width, "#", str_output + r"\w" + point[1], str_zones + "\\" + point[1],
                                          "#", "NONE", "MAINTAIN_EXTENT")
                    arcpy.Clip_management(str_zbed, "#", str_output + r"\d" + point[1], str_zones + "\\" + point[1],
                                          "#", "NONE", "MAINTAIN_EXTENT")
                    arcpy.Clip_management(str_manning, "#", str_output + r"\n" + point[1], str_zones + "\\" + point[1],
                                          "#", "NONE", "MAINTAIN_EXTENT")
                    arcpy.Clip_management(str_mask, "#", str_output + r"\m" + point[1], str_zones + "\\" + point[1],
                                          "#", "NONE", "MAINTAIN_EXTENT")

                    arcpy.RasterToASCII_conversion(str_zones + "\\" + point[1], str_output + "\\lisflood\\" + point[1] + ".txt" )
                    arcpy.RasterToASCII_conversion(str_output + "\d" + point[1],
                                                   str_output + "\\lisflood\\d" + point[1] + ".txt")
                    arcpy.RasterToASCII_conversion(str_output + "\w" + point[1],
                                               str_output + "\\lisflood\\w" + point[1] + ".txt")
                    arcpy.RasterToASCII_conversion(str_output + "\m" + point[1],
                                                  str_output + "\\lisflood\\m" + point[1] + ".txt")
                    arcpy.RasterToASCII_conversion(str_output + "\\n" + point[1],
                                                   str_output + "\\lisflood\\n" + point[1] + ".txt")




        return