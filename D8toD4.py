# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
# Mars 2017
#####################################################

from RasterIO import *


class D8toD4(object):
    def __init__(self):

        self.label = "D4 flow direction"
        self.description = "Transforme un flow direction D8 et D4 le long des écoulements"
        self.canRunInBackground = False


    def getParameterInfo(self):

        param_flowdir = arcpy.Parameter(
            displayName="Flow direction",
            name="flowdir",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_dem = arcpy.Parameter(
            displayName="MNE",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        param_frompoint = arcpy.Parameter(
            displayName="Points de départ",
            name="frompoint",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param_d4fd = arcpy.Parameter(
            displayName="Flow direction corrigé",
            name="d4fd",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Output")


        param_flowdir.value = r"D:\ProgrammationCSharp\PythonFlood\test\flowdir"
        param_frompoint.value = r"D:\ProgrammationCSharp\PythonFlood\test\Frompoints.shp"




        params = [param_flowdir, param_dem, param_frompoint, param_d4fd]

        return params

    def isLicensed(self):

        return True

    def updateParameters(self, parameters):

        return

    def updateMessages(self, parameters):

        return

    def execute(self, parameters, messages):

        # Récupération des paramètres
        str_flowdir = parameters[0].valueAsText
        str_dem = parameters[1].valueAsText
        str_frompoint = parameters[2].valueAsText
        SaveResult = parameters[3].valueAsText

        # Chargement des fichiers
        flowdir = RasterIO(arcpy.Raster(str_flowdir))
        dem = RasterIO(arcpy.Raster(str_dem))
        try:
            dem.checkMatch(flowdir)
        except Exception as e:
            messages.addErrorMessage(e.message)

        Result = RasterIO(arcpy.Raster(str_flowdir), SaveResult, int, -255)

        # Traitement effectué pour chaque point de départ
        frompointcursor = arcpy.da.SearchCursor(str_frompoint, "SHAPE@")
        for frompoint in frompointcursor:

            # On prend l'objet géométrique (le point) associé à la ligne dans la table
            frompointshape = frompoint[0].firstPoint

            # Conversion des coordonnées
            currentcol = flowdir.XtoCol(frompointshape.X)
            currentrow = flowdir.YtoRow(frompointshape.Y)


            intheraster = True
            # Tests de sécurité pour s'assurer que le point de départ est à l'intérieurs des rasters
            if currentcol<0 or currentcol>=flowdir.raster.width or currentrow<0 or currentrow>= flowdir.raster.height:
                intheraster = False
            elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                                flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow, currentcol) <> 8 and
                                flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
                intheraster = False

            # Traitement effectué sur chaque cellule le long de l'écoulement
            while (intheraster):

                # On regarde la valeur du "flow direction"
                direction = flowdir.getValue(currentrow, currentcol)

                # Si cette valeur est 1, 4, 16 ou 64, on se déplace sur des cases adjacentes. On garde la valeur.
                # Si cette valeur est 2, 8, 32 ou 128, on se déplace en diagonale. Un traitement est nécesaire.

                if (direction == 1):
                    Result.setValue(currentrow, currentcol, direction)
                    currentcol = currentcol + 1

                if (direction == 2):
                    # on regarde, parmi les deux cellules adjacentes pouvant remplacer le déplacement en diagonale, quelle est celle d'élévation la plus basse, et on passe par celle-ci
                    # exemple : direction = 2 -> on se déplace en diagonale, en bas à droite
                    # on peut donc remplacer ce déplacement par aller à droite (flow direction = 1) puis aller en bas (flow direction = 4) ou bien aller en bas puis aller à droite
                    if dem.getValue(currentrow, currentcol + 1) < dem.getValue(currentrow + 1, currentcol):
                        # La cellul à droite à une élévation plus basse que la cellule en bas, on choisie donc d'aller à droite puis ensuite en bas
                        # On modifie donc le flow direction pour aller à droite
                        Result.setValue(currentrow, currentcol, 1)
                        # Puis on modifie le flow direction du la cellule à droite pour aller en bas
                        Result.setValue(currentrow, currentcol+1, 4)
                    else:
                        Result.setValue(currentrow, currentcol, 4)
                        Result.setValue(currentrow+1, currentcol, 1)
                    currentcol = currentcol + 1
                    currentrow = currentrow + 1

                if (direction == 4):
                    Result.setValue(currentrow, currentcol, direction)
                    currentrow = currentrow + 1

                if (direction == 8):
                    if dem.getValue(currentrow+1, currentcol) < dem.getValue(currentrow, currentcol-1):
                        Result.setValue(currentrow, currentcol, 4)
                        Result.setValue(currentrow+1, currentcol, 16)
                    else:
                        Result.setValue(currentrow, currentcol, 16)
                        Result.setValue(currentrow, currentcol-1, 4)
                    currentcol = currentcol - 1
                    currentrow = currentrow + 1

                if (direction == 16):
                    Result.setValue(currentrow, currentcol, direction)
                    currentcol = currentcol - 1

                if (direction == 32):
                    if dem.getValue(currentrow-1, currentcol) < dem.getValue(currentrow, currentcol-1):
                        Result.setValue(currentrow, currentcol, 64)
                        Result.setValue(currentrow-1, currentcol, 16)
                    else:
                        Result.setValue(currentrow, currentcol, 16)
                        Result.setValue(currentrow, currentcol-1, 64)
                    currentcol = currentcol - 1
                    currentrow = currentrow - 1

                if (direction == 64):
                    Result.setValue(currentrow, currentcol, direction)
                    currentrow = currentrow - 1

                if (direction == 128):
                    if dem.getValue(currentrow-1, currentcol) < dem.getValue(currentrow, currentcol+1):
                        Result.setValue(currentrow, currentcol, 64)
                        Result.setValue(currentrow-1, currentcol, 1)
                    else:
                        Result.setValue(currentrow, currentcol, 1)
                        Result.setValue(currentrow, currentcol+1, 64)
                    currentcol = currentcol + 1
                    currentrow = currentrow - 1


                if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
                    intheraster = False
                elif (flowdir.getValue(currentrow, currentcol) <> 1 and flowdir.getValue(currentrow, currentcol) <> 2 and
                                flowdir.getValue(currentrow, currentcol) <> 4 and flowdir.getValue(currentrow, currentcol) <> 8 and
                                flowdir.getValue(currentrow, currentcol) <> 16 and flowdir.getValue(currentrow, currentcol) <> 32 and flowdir.getValue(currentrow, currentcol) <> 64 and flowdir.getValue(currentrow, currentcol) <> 128):
                    intheraster = False

                if intheraster:
                    if (Result.getValue(currentrow, currentcol) <> -255):
                        # Atteinte d'un confluent
                        intheraster = False




        Result.save()


        return