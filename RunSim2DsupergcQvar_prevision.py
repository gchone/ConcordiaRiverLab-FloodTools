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
# v1.4 - Séparation de l'interface

import os
import arcpy
import subprocess
import shutil
import csv
from RasterIO import *


def execute_RunSim_prev(str_zonefolder, str_simfolder, str_lisfloodfolder, str_csvq, str_lakes, field_z, voutput, simtime, channelmanning, str_log, messages):

    str_inbci = str_zonefolder + "\\inbci.shp"
    str_outbci = str_zonefolder + "\\outbci.shp"

    ref_raster = arcpy.Raster(str_zonefolder + "\\zone1")

    # count est utilisé pour compter le nombre de zones, pour la barre de progression lors des simulations
    count = 0

    bcipointcursor = arcpy.da.SearchCursor(str_inbci, ["SHAPE@", "zoneid", "flowacc", "type", "fpid"])
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


    allzones = list(dictsegmentsin.keys())
    allzones.sort()

    sortedzones = []
    listzones_fp = []
    lastidfp = -999
    for zone in allzones:

        if dictsegmentsin[zone][0][4] != lastidfp:
            if lastidfp!=-999:

                listzones_fp.sort(reverse=True)
                sortedzones.extend(listzones_fp)
            listzones_fp = []
            lastidfp = dictsegmentsin[zone][0][4]


        listzones_fp.append(zone)
    listzones_fp.sort(reverse=True)
    sortedzones.extend(listzones_fp)

    # Ajout des information du fichier outbci.shp
    listzonesout = {}
    bcipointcursor = arcpy.da.SearchCursor(str_outbci, ["zoneid", "side", "lim1", "lim2", "side2", "lim3", "lim4", "SHAPE@"])
    for point in bcipointcursor:
        listzonesout[point[0]] = point

    # SuperGC ou SubGC?
    zones = str_zonefolder + "\\envelopezones.shp"
    # récupération du paramètre SuperGC et bci lac
    typesim = {}
    zonesscursor = arcpy.da.SearchCursor(zones, ["GRID_CODE", "SHAPE@", "SuperGC", "Lake_ID"])
    lakeid_byzone = {}
    for zoneshp in zonesscursor:
        typesim[zoneshp[0]] = zoneshp[2]
        if zoneshp[3] != -999:
            lakeid_byzone[zoneshp[0]] = zoneshp[3]

    # Z BCI
    fieldidlakes = arcpy.Describe(str_lakes).OIDFieldName
    shplakes = arcpy.da.SearchCursor(str_lakes, [fieldidlakes, field_z])
    fieldz_bylakeid = {}
    for shplake in shplakes:
        fieldz_bylakeid[shplake[0]] = shplake[1]

    # Lancement de LISFLOOD-FP
    arcpy.SetProgressor("step", "Simulation 2D", 0, count, 1)
    progres = 0
    arcpy.SetProgressorPosition(progres)

    filelog = open(str_log, 'w')
    csvfile = open(str_csvq)
    csv_reader = csv.DictReader(csvfile)

    for cvsrow in csv_reader:
        simname = cvsrow["nom"]
        currentsimfolder = str_simfolder + "\\" + simname
        currentresult = str_simfolder + "\\res_" + simname
        simq = float(cvsrow["q"])

        if not os.path.isdir(currentsimfolder):
            os.makedirs(currentsimfolder)

        for zone in sortedzones:
            segment = dictsegmentsin[zone]
            for point in sorted(segment, key=lambda q: q[2]):

                if point[3]=="main":
                    try:
                        if not arcpy.Exists(currentsimfolder + "\\elev_zone" + str(point[1])):


                            outpointshape = listzonesout[point[1]][7].firstPoint

                            if point[1] in lakeid_byzone:
                                hfix = fieldz_bylakeid[lakeid_byzone[point[1]]]

                            else:
                                if not os.path.exists(currentresult):
                                    messages.addErrorMessage("Condition limite aval non trouvée : zone " + str(point[1]))
                                else:
                                    # issue with Mosaic_management, used later with lisflood_res:
                                    # crash sometimes if the file is read here
                                    # so we make a tmp copy
                                    if arcpy.Exists(currentsimfolder + "\\tmp_zone"  + str(point[1])):
                                        arcpy.Delete_management(currentsimfolder + "\\tmp_zone"  + str(point[1]))
                                    arcpy.Copy_management(currentresult, currentsimfolder + "\\tmp_zone" + str(point[1]))
                                    res_downstream = RasterIO(arcpy.Raster(currentsimfolder + "\\tmp_zone"  + str(point[1])))
                                    hfix = res_downstream.getValue(res_downstream.YtoRow(outpointshape.Y), res_downstream.XtoCol(outpointshape.X))
                                    if hfix == res_downstream.nodata:
                                        messages.addErrorMessage("Condition limite aval non trouvée : zone " + str(point[1]))
                                    arcpy.Delete_management(currentsimfolder + "\\tmp_zone"  + str(point[1]))

                            zonedem = RasterIO(arcpy.Raster(str_zonefolder + "\\zone" + str(point[1])))
                            zdem = zonedem.getValue(zonedem.YtoRow(outpointshape.Y),
                                                    zonedem.XtoCol(outpointshape.X))


                            # par

                            newfile = str_simfolder + "\\zone" + str(point[1]) + ".par"
                            if os.path.isfile(newfile):
                                os.remove(newfile)

                            filepar = open(newfile, 'w')
                            filepar.write("DEMfile\tzone" + str(point[1]) + ".txt\n")
                            filepar.write("resroot\tzone" + str(point[1]) + "\n")
                            filepar.write("dirroot\t" + simname + "\n")
                            filepar.write("manningfile\tnzone" + str(point[1]) + ".txt\n")
                            filepar.write("bcifile\tzone" + str(point[1]) + ".bci" + "\n")
                            filepar.write("sim_time\t" + str(simtime) + "\n")
                            filepar.write("saveint\t" + str(simtime) + "\n")
                            filepar.write("bdyfile\t"+ simname +"\\zone" + str(point[1]) + ".bdy" + "\n")
                            filepar.write("SGCwidth\twzone" + str(point[1]) + ".txt\n")
                            filepar.write("SGCbank\tzone" + str(point[1]) + ".txt\n")
                            filepar.write("SGCbed\tdzone" + str(point[1]) + ".txt\n")
                            filepar.write("SGCn\t" + str(channelmanning) + "\n")
                            if typesim[point[1]] == 1:
                                filepar.write("chanmask\tmzone" + str(point[1]) + ".txt\n")

                            # Vitesses du courant
                            if voutput:
                                filepar.write("hazard\n")
                                filepar.write("qoutput\n")
                            filepar.write("cfl\t0.5\n")
                            filepar.write("max_Froude\t1\n")
                            # filepar.write("debug\n")
                            filepar.close()

                            # bdy
                            newfilebdy = currentsimfolder + "\\zone" + str(point[1]) + ".bdy"

                            for point2 in sorted(segment, key=lambda q: q[2]):

                                q_value = point2[2]*simq/(ref_raster.meanCellHeight*ref_raster.meanCellWidth)

                                if point2[3] == "main":
                                    # Création du fichier bdy


                                    pointdischarge = q_value / (
                                    (zonedem.raster.meanCellHeight + zonedem.raster.meanCellWidth) / 2)
                                    lastdischarge = q_value
                                    latnum = 0
                                    filebdy = open(newfilebdy, 'w')
                                    filebdy.write("zone"+str(point[1]) + ".bdy\n")
                                    filebdy.write("zone"+str(point[1]) + "\n")
                                    filebdy.write("3\tseconds\n")
                                    filebdy.write("0\t0\n")
                                    filebdy.write("{0:.3f}".format(pointdischarge) + "\t50000\n")
                                    filebdy.write("{0:.3f}".format(pointdischarge) + "\t" + str(simtime))
                                    filebdy.close()
                                else:
                                    latnum += 1
                                    pointdischarge = (q_value - lastdischarge) / (
                                    (zonedem.raster.meanCellHeight + zonedem.raster.meanCellWidth) / 2)
                                    lastdischarge = q_value
                                    filebdy = open(newfilebdy, 'a')
                                    filebdy.write("\nzone" + str(point[1]) + "_" + str(latnum) + "\n")
                                    filebdy.write("3\tseconds\n")
                                    filebdy.write("0\t0\n")
                                    filebdy.write("{0:.3f}".format(pointdischarge) + "\t50000\n")
                                    filebdy.write("{0:.3f}".format(pointdischarge) + "\t" + str(simtime))
                                    filebdy.close()

                            filebdy = open(newfilebdy, 'a')
                            filebdy.write("\nhvar\n")
                            filebdy.write("4\tseconds\n")
                            filebdy.write("{0:.2f}".format(zdem) + "\t0\n")
                            filebdy.write("{0:.2f}".format(zdem) + "\t50000\n")
                            filebdy.write("{0:.2f}".format(hfix) + "\t55000\n")
                            filebdy.write("{0:.2f}".format(hfix) + "\t" + str(simtime))

                            filebdy.close()

                            subprocess.check_call([str_lisfloodfolder + "\\lisflood_intelRelease_double.exe", "-steady", "-steadytol", steadytol[point[1]], str_simfolder + "\\zone" + str(point[1]) + ".par"], shell=True, cwd=str_simfolder)
                            progres += 1
                            arcpy.SetProgressorPosition(progres)



                            # Conversion des fichiers output

                            # on renomme les fichiers créés (nécessaire pour être acceptés par l'outil de convsersion ASCII vers raster)
                            zonename = "zone"+str(point[1])

                            if os.path.exists(currentsimfolder + "\\"  + zonename + "elev.txt"):
                                os.remove(currentsimfolder + "\\"   + zonename + "elev.txt")

                            if os.path.exists(currentsimfolder   + "\\" + zonename + "-9999.elev"):
                                os.rename(currentsimfolder  + "\\"  + zonename + "-9999.elev",
                                          currentsimfolder + "\\" + zonename + "elev.txt")
                            else:
                                os.rename(currentsimfolder  + "\\" + zonename + "-0001.elev",
                                          currentsimfolder + "\\" + zonename + "elev.txt")
                                messages.addWarningMessage("Steady state not reached : " + zonename)

                            if os.path.exists(currentsimfolder + "\\" + zonename + "-9999.Vx") or os.path.exists(currentsimfolder + "\\"  + zonename + "-0001.Vx"):
                                if os.path.exists(currentsimfolder + "\\" + zonename + "Vx.txt"):
                                    os.remove(currentsimfolder + "\\" + zonename + "Vx.txt")

                                if os.path.exists(currentsimfolder + "\\" + zonename + "Vy.txt"):
                                    os.remove(currentsimfolder + "\\" + zonename + "Vy.txt")
                                if os.path.exists(currentsimfolder  + "\\" + zonename + "-9999.Vx"):
                                    os.rename(currentsimfolder  + "\\" + zonename + "-9999.Vx",
                                              currentsimfolder+ "\\" + zonename + "Vx.txt")
                                    os.rename(currentsimfolder  + "\\"  + zonename + "-9999.Vy",
                                              currentsimfolder  + "\\" + zonename + "Vy.txt")
                                else:
                                    os.rename(currentsimfolder  + "\\" + zonename + "-0001.Vx",
                                              currentsimfolder  + "\\" + zonename + "Vx.txt")
                                    os.rename(currentsimfolder  + "\\" + zonename + "-0001.Vy",
                                              currentsimfolder  + "\\" + zonename + "Vy.txt")
                                arcpy.ASCIIToRaster_conversion(currentsimfolder  + "\\" + zonename + "Vx.txt",
                                                               currentsimfolder + "\\Vx_" + zonename,
                                                           "FLOAT")
                                arcpy.ASCIIToRaster_conversion(currentsimfolder  + "\\" + zonename + "Vy.txt",
                                                               currentsimfolder + "\\Vy_" + zonename,
                                                           "FLOAT")
                                arcpy.DefineProjection_management(currentsimfolder + "\\Vx_" + zonename, ref_raster.spatialReference)
                                arcpy.DefineProjection_management(currentsimfolder + "\\Vy_" + zonename, ref_raster.spatialReference)


                            # Conversion des fichiers de sortie en raster pour ArcGIS
                            str_elev = currentsimfolder + "\\elev_" + zonename
                            arcpy.ASCIIToRaster_conversion(currentsimfolder + "\\"  + zonename + "elev.txt", str_elev, "FLOAT")


                            # Ajout de la projection
                            arcpy.DefineProjection_management(str_elev, ref_raster.spatialReference)



                        if not arcpy.Exists(currentresult):

                            arcpy.Copy_management(currentsimfolder + "\\elev_" + "zone"+str(point[1]), currentresult)
                        else:

                            arcpy.Mosaic_management(currentsimfolder + "\\elev_" + "zone"+str(point[1]), currentresult, mosaic_type="MAXIMUM")
                            #arcpy.Copy_management(str_output + "\\lisflood_res", str_output + "\\tmp_mosaic")
                            #arcpy.Delete_management(str_output + "\\lisflood_res")
                            # arcpy.MosaicToNewRaster_management(';'.join([str_output + "\\tmp_mosaic", str_output + "\\elev_" + point[1]]),
                            #                                    str_output,"lisflood_res",
                            #                                    pixel_type="32_BIT_FLOAT",
                            #                                    number_of_bands=1)

                    except BaseException as e:
                        filelog.write("ERREUR in " + simname + ": sim aborded during zone "+ str(point[1]) + "\n")
                        messages.addWarningMessage("Some simulations skipped. See log file.")
    return

