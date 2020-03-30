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

import os
import arcpy
import subprocess
import shutil
from RasterIO import *



class RunSim2DsupergcQvar_hdown(object):
    def __init__(self):

        self.label = "SuperGC Q raster H_DOWN"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):


        param_flowdir = arcpy.Parameter(
            displayName="Flow direction",
            name="flowdir",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_zones = arcpy.Parameter(
            displayName="Dossier des zones",
            name="zones",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        param_lisflood = arcpy.Parameter(
            displayName="Dossier du programme LISFLOOD-FP",
            name="lisflood",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param_output = arcpy.Parameter(
            displayName="Dossier de sortie",
            name="folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")




        params = [param_flowdir, param_zones, param_lisflood, param_output]

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
        str_flowdir = parameters[0].valueAsText
        str_zones = parameters[1].valueAsText
        str_lisflood = parameters[2].valueAsText
        str_output = parameters[3].valueAsText

        str_inbci = str_zones + "\\inbci.shp"
        str_outbci = str_zones + "\\outbci.shp"

        # Création des dossiers de sortie s'ils n'existent pas
        if not os.path.isdir(str_output):
            os.makedirs(str_output)
        if not os.path.isdir(str_output + "\\lisflood\\"):
            os.makedirs(str_output + "\\lisflood\\")


        flowdir = arcpy.Raster(str_flowdir)

        # count est utilisé pour compter le nombre de zones, pour la barre de progression lors des simulations
        count = 0

        bcipointcursor = arcpy.da.SearchCursor(str_inbci, ["SHAPE@", "zone", "discharge", "type", "fpid"])
        dictsegmentsin = {}

        steadytol = {}

        for point in bcipointcursor:
            if point[1] not in dictsegmentsin:
                dictsegmentsin[point[1]] = []
            dictsegmentsin[point[1]].append(point)
            if point[3] == "main":
                if point[2] > 100:
                    steadytol[point[1]] = "1"
                else:
                    steadytol[point[1]] = "0.1"


        allzones = dictsegmentsin.keys()
        allzones.sort(key=lambda k: int(k[4:]))

        sortedzones = []
        listzones_fp = []
        lastidfp = -999
        for zone in allzones:
            print dictsegmentsin[zone][0][4]
            if dictsegmentsin[zone][0][4] != lastidfp:
                if lastidfp!=-999:
                    print listzones_fp
                    listzones_fp.sort(key=lambda k: int(k[4:]), reverse=True)
                    sortedzones.extend(listzones_fp)
                listzones_fp = []
                lastidfp = dictsegmentsin[zone][0][4]


            listzones_fp.append(zone)
        listzones_fp.sort(key=lambda k: int(k[4:]), reverse=True)
        sortedzones.extend(listzones_fp)

        # Ajout des information du fichier outbci.shp
        listzonesout = {}
        bcipointcursor = arcpy.da.SearchCursor(str_outbci, ["zone", "side", "lim1", "lim2", "side2", "lim3", "lim4", "ws", "SHAPE@"])
        for point in bcipointcursor:
            if not os.path.exists(str_output + "\\mxe_" + point[0]):
                listzonesout[point[0]] = point

        # Lancement de LISFLOOD-FP
        arcpy.SetProgressor("step", "Simulation 2D", 0, count, 1)
        progres = 0
        arcpy.SetProgressorPosition(progres)

        if os.path.exists(str_output + "\\lisflood_res"):
            arcpy.Delete_management(str_output + "\\lisflood_res")
            
        for zone in sortedzones:
            segment = dictsegmentsin[zone]
            for point in sorted(segment, key=lambda q: q[2]):

                if point[3]=="main":
                    if not arcpy.Exists(str_output + "\\elev_" + point[1]):


                        # le bci devrait être complété dans PrepaSim2D, pas ici
                        newfile = str_output + "\\lisflood\\" + point[1] + ".bci"
                        if os.path.exists(newfile):
                            os.remove(newfile)
                        shutil.copy(str_output + "\\lisflood\\" + point[1] + "prepa.bci", newfile)

                        filebci = open(newfile, 'a')
                        filebci.write(
                            listzonesout[point[1]][1] + "\t" + str(listzonesout[point[1]][2]) + "\t" + str(
                                listzonesout[point[1]][3]) + "\tHVAR\thvar")
                        if str(listzonesout[point[1]][4]) != "0":
                            filebci.write("\n" + str(listzonesout[point[1]][4]) + "\t" + str(
                                listzonesout[point[1]][5]) + "\t" + str(
                                listzonesout[point[1]][6]) + "\tHVAR\thvar")
                        filebci.close()

                        outpointshape = listzonesout[point[1]][8].firstPoint
                        if listzonesout[point[1]][7] != -999:
                            hfix = listzonesout[point[1]][7]
                        else:
                            if not os.path.exists(str_output + "\\lisflood_res"):
                                messages.addErrorMessage("Condition limite aval non trouvée : " + point[1])
                            else:
                                # issue with Mosaic_management, used later with lisflood_res:
                                # crash sometimes if the file is read here
                                # so we make a tmp copy
                                if arcpy.Exists(str_output + "\\tmp_"  + point[1]):
                                    arcpy.Delete_management(str_output + "\\tmp_"  + point[1])
                                arcpy.Copy_management(str_output + "\\lisflood_res", str_output + "\\tmp_" + point[1])
                                res_downstream = RasterIO(arcpy.Raster(str_output + "\\tmp_"  + point[1]))
                                hfix = res_downstream.getValue(res_downstream.YtoRow(outpointshape.Y), res_downstream.XtoCol(outpointshape.X))
                                if hfix == res_downstream.nodata:
                                    messages.addErrorMessage("Condition limite aval non trouvée : " + point[1])
                                arcpy.Delete_management(str_output + "\\tmp_"  + point[1])

                        zonedem = RasterIO(arcpy.Raster(str_zones + "\\" + point[1]))
                        zdem = zonedem.getValue(zonedem.YtoRow(outpointshape.Y),
                                                zonedem.XtoCol(outpointshape.X))


                        # bdy
                        newfile = str_output + "\\lisflood\\" + point[1] + ".bdy"
                        if os.path.exists(newfile):
                            os.remove(newfile)
                        shutil.copy(str_output + "\\lisflood\\" + point[1] + "prepa.bdy", newfile)

                        filebdy = open(newfile, 'a')
                        filebdy.write("\nhvar\n")
                        filebdy.write("4\tseconds\n")
                        filebdy.write("{0:.2f}".format(zdem) + "\t0\n")
                        filebdy.write("{0:.2f}".format(zdem) + "\t50000\n")
                        filebdy.write("{0:.2f}".format(hfix) + "\t55000\n")
                        filebdy.write("{0:.2f}".format(hfix) + "\t" + str(simtime))

                        filebdy.close()

                        subprocess.check_call([str_lisflood + "\\lisflood_intelRelease_double.exe", "-steady", "-steadytol", steadytol[point[1]], str_output + "\\lisflood\\" + point[1] + ".par"], shell=True, cwd=str_output + "\\lisflood")
                        progres += 1
                        arcpy.SetProgressorPosition(progres)



                        # Test des conditions d'écoulement continu (Qin = Qout) et conversion des fichiers output

                        # lecture du fichier .mass
                        newfile = str_output + "\\lisflood\\res\\" + point[1] + ".mass"
                        file = open(newfile, 'r')
                        # on cherche la dernière ligne
                        for line in file:
                            pass
                        file.close()
                        # on regarde les éléments de la dernière ligne du fichier .mass
                        # elems[6] est le débit d'entré (constant pendant la simulation) et elems[8] est le débit de sortie à la fin de la simulation
                        elems = line.split()
                        if float(elems[6]) != 0:
                            # Avertissement si le débit de sortie n'est pas à + ou - 5% du débit d'entré
                            if abs(float(elems[6]) - float(elems[8])) / float(elems[6]) > 0.05:
                                messages.addWarningMessage("{0}: condition d'écoulement continue non respectée".format(point[1]))
                        # on renomme les fichiers créés (nécessaire pour être acceptés par l'outil de convsersion ASCII vers raster)
                        if os.path.exists(str_output + "\\lisflood\\res\\"  + point[1] + "elev.txt"):
                            os.remove(str_output + "\\lisflood\\res\\"  + point[1] + "elev.txt")

                        if os.path.exists(str_output + "\\lisflood\\res\\"  + point[1] + "-9999.elev"):
                            os.rename(str_output + "\\lisflood\\res\\"  + point[1] + "-9999.elev",
                                      str_output + "\\lisflood\\res\\" + point[1] + "elev.txt")
                        else:
                            os.rename(str_output + "\\lisflood\\res\\"  + point[1] + "-0001.elev",
                                      str_output + "\\lisflood\\res\\" + point[1] + "elev.txt")
                            messages.addWarningMessage("Steady state not reached : " + point[1])
                            
                        if os.path.exists(str_output + "\\lisflood\\res\\"  + point[1] + "-9999.Vx") or os.path.exists(str_output + "\\lisflood\\res\\"  + point[1] + "-0001.Vx"):
                            if os.path.exists(str_output + "\\lisflood\\res\\"  + point[1] + "Vx.txt"):
                                os.remove(str_output + "\\lisflood\\res\\"  + point[1] + "Vx.txt")
             
                            if os.path.exists(str_output + "\\lisflood\\res\\"  + point[1] + "Vy.txt"):
                                os.remove(str_output + "\\lisflood\\res\\"  + point[1] + "Vy.txt")
                            if os.path.exists(str_output + "\\lisflood\\res\\"  + point[1] + "-9999.Vx"):
                                os.rename(str_output + "\\lisflood\\res\\"  + point[1] + "-9999.Vx",
                                          str_output + "\\lisflood\\res\\" + point[1] + "Vx.txt")
                                os.rename(str_output + "\\lisflood\\res\\"  + point[1] + "-9999.Vy",
                                          str_output + "\\lisflood\\res\\" + point[1] + "Vy.txt")
                            else:
                                os.rename(str_output + "\\lisflood\\res\\"  + point[1] + "-0001.Vx",
                                          str_output + "\\lisflood\\res\\" + point[1] + "Vx.txt")
                                os.rename(str_output + "\\lisflood\\res\\"  + point[1] + "-0001.Vy",
                                          str_output + "\\lisflood\\res\\" + point[1] + "Vy.txt")
                            arcpy.ASCIIToRaster_conversion(str_output + "\\lisflood\\res\\" + point[1] + "Vx.txt",
                                                       str_output + "\\Vx_" + point[1],
                                                       "FLOAT")
                            arcpy.ASCIIToRaster_conversion(str_output + "\\lisflood\\res\\" + point[1] + "Vy.txt",
                                                       str_output + "\\Vy_" + point[1],
                                                       "FLOAT")
                            arcpy.DefineProjection_management(str_output + "\\Vx_" + point[1], flowdir.spatialReference)
                            arcpy.DefineProjection_management(str_output + "\\Vy_" + point[1], flowdir.spatialReference)
                            

                        # Conversion des fichiers de sortie en raster pour ArcGIS
                        str_elev = str_output + "\\elev_" + point[1]
                        arcpy.ASCIIToRaster_conversion(str_output + "\\lisflood\\res\\" + point[1] + "elev.txt", str_elev, "FLOAT")


                        # Ajout de la projection
                        arcpy.DefineProjection_management(str_output + "\\elev_" + point[1], flowdir.spatialReference)




                    if not arcpy.Exists(str_output + "\\lisflood_res"):

                        arcpy.Copy_management(str_output + "\\elev_" + point[1], str_output + "\\lisflood_res")
                    else:
                        print str(point[1]) + " done"

                        arcpy.Mosaic_management(str_output + "\\elev_" + point[1], str_output + "\\lisflood_res", mosaic_type="MAXIMUM")
                        #arcpy.Copy_management(str_output + "\\lisflood_res", str_output + "\\tmp_mosaic")
                        #arcpy.Delete_management(str_output + "\\lisflood_res")
                        # arcpy.MosaicToNewRaster_management(';'.join([str_output + "\\tmp_mosaic", str_output + "\\elev_" + point[1]]),
                        #                                    str_output,"lisflood_res",
                        #                                    pixel_type="32_BIT_FLOAT",
                        #                                    number_of_bands=1)

        return

class param:
    def __init__(self, value):
        self.valueAsText = value

if __name__ == "__main__":
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True

    params = []
    params.append(param(r"F:\MSP2\JacquesCartier\newDEMmars2019\withStreamBurning\flowdir"))
    params.append(param(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\zones_hdown_test2"))
    params.append(param(r"D:\MSP\LISFLOOD-FP\LISFLOOD_FP_v7c"))
    params.append(param(r"F:\MSP2\JacquesCartier\newDEMmars2019\versionAout2019\modifOctobre2019\h_down_sim2"))

    arcpy.env.scratchWorkspace = r"F:\MSP2\JacquesCartier\tmp"

    RunSim2DsupergcQvar_hdown().execute(params, None)
