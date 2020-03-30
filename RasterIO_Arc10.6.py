# coding: latin-1

#####################################################
# Gu�nol� Chon�
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Mars 2017 - Cr�ation
# v1.1 - Juillet 2018 - Utilisation d'un processus ind�pendant pour enregistrer les rasters, fusion avec RasterIOXL,
#   modification des noms de raster cr��s, d�bogage utilisation avec raster source
# v1.2 - Juillet 2018 - Debogage
# v1.3 - Ao�t 2019 - D�gogage
# v1.3.1 - Septembre 2019 - D�gogage: D�calage de 1 pixel pour les versions ArcGIS 1.6(?) ou sup.

# Ce code est une biblioth�que g�n�rale pour la gestion des matrices (rasters)

# R�f�rence:
# Ce code a �t� cr�� � partir du code exemple fourni avec l'aide de NumPyArrayToRaster:
# http://desktop.arcgis.com/fr/arcmap/10.4/analyze/arcpy-functions/numpyarraytoraster-function.htm

# La classe RasterIO permet de g�rer les op�rations de lecture et d'�criture sur les objects de type Raster par les fonctions suivantes:
#  - getValue(row, col) : permet de lire la valeur d'une cellule du raster
#  - setValue(row, col, value) : permet d'enregistrer la valeur d'une cellule du raster
#  - save() : enregistre dans le fichier d�sign� les modifications apport�es par la fonction setValue
# RasterIO peut etre utilis� pour g�rer un fichier existant (pour y lire ou y �crire des donn�es), ou bien pour cr�er un nouveau raster
# Dans le premier cas, seul le param�tre "raster" (object de type Raster) doit �tre fourni au constructeur
# Dans le dernier cas, les param�tres suivants doivent �tre fournis au constructeur:
#  - "raster" (object de type Raster) : Raster utilis� comme mod�le pour le nouveau raster � cr�er.
# Le nouveau raster couvrira la m�me zone, avec la m�me r�solution, et aura le m�me syst�me de coordonn�es, que le raster utilis� comme mod�le
#  - "fileout" (cha�ne) : chemin complet et nom du fichier � cr�er
#  - "dtype" : peut �tre mis � "int" ou "float". Type de donn�es pour le raster � cr�er.
#  - "default" : valeur par d�faut (valeur de "NoData") utilis�e pour le raster

# RasterIO fournit �galement les fonctions utilitaires suivantes:
#  - checkMatch(other_RasterIO) : permet de s'assurer que deux rasters couvrent la m�me zone avec la m�me r�solution
#  - XtoCol, YtoRow, ColtoX et RowtoY : permettent de convertir des coordonn�es en une position dans la matrice, et inversement

# RasterIOfull fonctionne sur les principes suivants:
#  - Lorsqu'une premi�re valeur est lue dans le raster, seule une section du raster est charg�e en m�moire (de taille blocksize), centr�e sur la cellule interrog�e
#  - Cette section n'est chang�e que lorsqu'on souhaite lire une valeur en dehors
#  - Les modification faites au raster sont conserv�es en m�moire (au lieu d'�tre �crites imm�diatement sur le disque)
#  - Si la quantit� de modification devient trop volumineuse, celles-ci sont alors enregistr�es sur le disque



import arcpy, numpy, math, os, argparse, pickle
import subprocess, sys, binascii

class RasterIO:

    # Lignes � modifier pour utiliser la gestion simple des raster (RasterIOlight, plus rapide) ou la gestion des rasters
    #  de grande taille (RasterIOfull)
    __managerclass = "RasterIOfull"
    #__managerclass = "RasterIOlight"


    def __init__(self, raster, fileout=None, dtype=int, default=-255):
        if self.__managerclass == "RasterIOlight":
            self.__rastermanager = RasterIOlight(raster, fileout, dtype, default)
        if self.__managerclass == "RasterIOfull":
            self.__rastermanager = RasterIOfull(raster, fileout, dtype, default)

    def checkMatch(self, other_rasterIO):
        # Check if two rasterIO have the same extent and same resolution
        # Rounding was necessary because, for unknown reasons, some produced rasters have slightly differents extents (less than a millimeter error)
        if (round(self.raster.extent.XMin, 3) != round(other_rasterIO.raster.extent.XMin, 3) or round(self.raster.extent.YMin, 3) != round(other_rasterIO.raster.extent.YMin, 3) or
            round(self.raster.extent.XMax, 3) != round(other_rasterIO.raster.extent.XMax, 3) or
            round(self.raster.extent.YMax, 3) != round(other_rasterIO.raster.extent.YMax, 3) or
            self.raster.height != other_rasterIO.raster.height or
            self.raster.width != other_rasterIO.raster.width):
            raise Exception("Input rasters must have same size and resolution")

    def XtoCol(self, X):
        return int(math.floor((X - self.rasterlike.extent.XMin) / self.rasterlike.meanCellWidth))
    def YtoRow(self, Y):
        return int(self.rasterlike.height - math.floor((Y - self.rasterlike.extent.YMin) / self.rasterlike.meanCellHeight) - 1)
    def ColtoX(self, col):
        return self.rasterlike.extent.XMin + (col + 0.5) * self.rasterlike.meanCellWidth
    def RowtoY(self, row):
        return self.rasterlike.extent.YMax - (row + 0.5) * self.rasterlike.meanCellHeight

    # Redirecting calls to methods getValue, setValue, and save to the __rastermanager
    def __getattr__(self, name):
        return getattr(self.__rastermanager, name)


class RasterIOlight:



    def __init__(self, raster, fileout=None, dtype = int, default = -255):
        if fileout is not None:
            self.rasterlike = raster
            self.raster = None
            self.nodata = default
            self.fileout = fileout
            self.dtype = dtype
            self.block = numpy.full([raster.height, raster.width], default, dtype)

        else:
            self.raster = raster
            self.rasterlike = raster
            self.nodata = raster.noDataValue
            self.block = arcpy.RasterToNumPyArray(self.raster)


    def getValue(self, row, col):

        return self.block[row, col]


    def setValue(self, row, col, value):

        self.block[row, col] = value


    def save(self):

        raster = arcpy.NumPyArrayToRaster(self.block, arcpy.Point(self.rasterlike.extent.XMin, self.rasterlike.extent.YMin),
                                                         self.rasterlike.meanCellWidth,
                                                         self.rasterlike.meanCellHeight, self.nodata)
        raster.save(self.fileout)

        self.raster = arcpy.Raster(self.fileout)
        arcpy.DefineProjection_management(self.raster, self.rasterlike.spatialReference)



class RasterIOfull:

    # Taille des rasters en m�moire. � modifier selon la m�moire disponible
    blocksize = 4096

    def __init__(self, raster, fileout=None, dtype = int, default = -255):
        if fileout is not None:
            self.rasterlike = raster
            self.raster = None
            self.nodata = default
            self.fileout = fileout
            self.dtype = dtype
        else:
            self.raster = raster
            self.rasterlike = raster
            self.nodata = raster.noDataValue
            if self.raster.pixelType == "U1":
                self.dtype = bool
            elif self.raster.pixelType == "F32" or self.raster.pixelType == "F64":
                self.dtype = float
            else:
                self.dtype = int
            self.fileout = raster.catalogPath


        self.block = None
        self.xblock = 0
        self.yblock = 0
        self.dict = {}
        self.dictsize = 0

    def getValue(self, row, col):

        # En dehors du raster
        if row <0 or col <0 or row >= self.rasterlike.height or col>=self.rasterlike.width:
            return self.nodata
        # La valeur a �t� chang�e en buffer
        if row in self.dict.keys():
            if col in self.dict[row].keys():
                return self.dict[row][col]
        # Pas de raster d'enregistr� et la valeur n'est pas en buffer
        if self.raster is None:
            return self.nodata



        # Raster enregistr� mais valeur pas dans le block
        if self.block is None or col < self.xblock or col >= self.xblock + self.blocksize or row < self.yblock or row >= self.yblock + self.blocksize:
            # Charger un nouveau block en m�moire
            del self.block
            # Upper left coordinate of block (in cells)
            self.xblock = max(0, col - self.blocksize/2)
            self.yblock = max(0, row - self.blocksize/2)
            # Lower left coordinate of block (in map units)
            mx = self.raster.extent.XMin + self.xblock*self.raster.meanCellWidth
            my = max(self.raster.extent.YMin, self.raster.extent.YMax - (self.blocksize + self.yblock)*self.raster.meanCellHeight)
            # Lower right coordinate of block (in cells)
            lx = min([self.xblock + self.blocksize, self.raster.width])
            ly = min([self.yblock + self.blocksize, self.raster.height])

            self.block = arcpy.RasterToNumPyArray(self.raster, arcpy.Point(mx, my), lx - self.xblock, ly - self.yblock, self.nodata)
            print self.block.shape



        # Prendre la valeur dans le block
        value = self.block[row - self.yblock, col - self.xblock]
        if self.raster is not None:
            if value == self.raster.noDataValue:
                return self.nodata
        return value


    def setValue(self, row, col, value):
        if row not in self.dict.keys():
            self.dict.update({row:{}})
        if col not in self.dict[row].keys():
            self.dictsize += 1
        self.dict[row].update({col:value})

        # Sauvegarde quand le dictionnaire est trop gros (taille du dictionnaire approximative)

        if self.dictsize > (self.blocksize*self.blocksize/2):
            self.save()
            self.dict = {}
            self.dictsize = 0


    def save(self):
        # Set environmental variables for output
        arcpy.env.outputCoordinateSystem = self.rasterlike.catalogPath
        arcpy.env.cellSize = self.rasterlike.catalogPath

        # Loop over data blocks
        filelist = []
        blockno = 0
        randomname = binascii.hexlify(os.urandom(6))
        picklefilename = arcpy.env.scratchWorkspace + "\\" + randomname + ".pkl"
        pickledict = open(picklefilename, 'wb')
        pickle.dump(self.dict, pickledict)
        pickledict.close()

        for x in range(0, self.rasterlike.width, self.blocksize):
            for y in range(0, self.rasterlike.height, self.blocksize):

                # Save on disk with a random name
                randomname = binascii.hexlify(os.urandom(6))
                filetemp = arcpy.env.scratchWorkspace + "\\" + randomname
                if self.raster is not None:
                    startcmd = "python.exe \""+sys.path[0].encode('utf-8')+"\\RasterIO.py\"" \
                               + " -rasterlike \"" + self.rasterlike.catalogPath.encode('utf-8') + "\""\
                               + " -x " + str(x) \
                               + " -y " + str(y) \
                               + " -blocksize " + str(self.blocksize) \
                               + " -blockname \"" + str(filetemp)  + "\""\
                               + " -nodata " + str(self.nodata) \
                               + " -dtype " + str(self.dtype.__name__) \
                               + " -pickledict \"" + picklefilename.encode('utf-8') + "\""\
                               + " -raster \"" + self.raster.catalogPath.encode('utf-8') + "\""
                else:
                    startcmd = "python.exe \""+sys.path[0].encode('utf-8')+"\\RasterIO.py\"" \
                               + " -rasterlike \"" + self.rasterlike.catalogPath.encode('utf-8') + "\""\
                               + " -x " + str(x) \
                               + " -y " + str(y) \
                               + " -blocksize " + str(self.blocksize) \
                               + " -blockname \"" + str(filetemp)  + "\""\
                               + " -nodata " + str(self.nodata) \
                               + " -dtype " + str(self.dtype.__name__) \
                               + " -pickledict \"" + picklefilename.encode('utf-8') + "\""

                FNULL = open(os.devnull, 'w')
                si = subprocess.STARTUPINFO()
                si.dwFlags = subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
                subprocess.check_call(startcmd, startupinfo=si, stdout=FNULL, stderr=subprocess.STDOUT)

                # Maintain a list of saved temporary files
                filelist.append(filetemp)
                blockno += 1

        os.remove(picklefilename)

        if arcpy.Exists(self.fileout):
            arcpy.Delete_management(self.fileout)

        if len(filelist) > 1:
            # Mosaic temporary files
            rastertype = {"U1": "1_BIT",
                          "U2": "2_BIT",
                          "U4": "4_BIT",
                          "U8": "8_BIT_UNSIGNED",
                          "S8": "8_BIT_SIGNED",
                          "U16": "16_BIT_UNSIGNED",
                          "S16": "16_BIT_SIGNED",
                          "U32": "32_BIT_UNSIGNED",
                          "S32": "32_BIT_SIGNED",
                          "F32": "32_BIT_FLOAT",
                          "F64": "64_BIT_FLOAT"}

            arcpy.MosaicToNewRaster_management(';'.join(filelist), os.path.dirname(os.path.abspath(self.fileout)),
                                               os.path.basename(self.fileout),
                                               pixel_type=rastertype[arcpy.Raster(filelist[0]).pixelType],
                                               number_of_bands=1)


        else:
            arcpy.Copy_management(filelist[0], self.fileout)

        # if len(filelist) > 1:
        #     # Mosaic temporary files
        #     arcpy.Mosaic_management(';'.join(filelist[1:]), filelist[0])
        #
        # arcpy.Copy_management(filelist[0], self.fileout)

        # Remove temporary files
        for fileitem in filelist:
            if arcpy.Exists(fileitem):
                arcpy.Delete_management(fileitem)

        self.raster = arcpy.Raster(self.fileout)
        if self.raster.pixelType == "U1":
            self.dtype = bool
        elif self.raster.pixelType == "F32" or self.raster.pixelType == "F64":
            self.dtype = float
        else:
            self.dtype = int

        arcpy.DefineProjection_management(self.raster, self.rasterlike.spatialReference)





if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-rasterlike', dest='rasterlike')
    parser.add_argument('-x', dest='x', type=int)
    parser.add_argument('-y', dest='y', type=int)
    parser.add_argument('-blocksize', dest='blocksize', type=int)
    parser.add_argument('-blockname', dest='blockname')
    parser.add_argument('-nodata', dest='nodata', type=float)
    parser.add_argument('-dtype', dest='dtypename')
    parser.add_argument('-pickledict', dest='pickledict')
    parser.add_argument('-raster', dest='raster')
    args = parser.parse_args()
    rasterlike = arcpy.Raster(args.rasterlike)
    raster = None
    if args.raster:
        raster = arcpy.Raster(args.raster)

    # Save on disk temporarily
    filetemp = args.blockname

    # Lower left coordinate of block (in map units)
    mx = rasterlike.extent.XMin + args.x * rasterlike.meanCellWidth
    my = max(rasterlike.extent.YMin,
             rasterlike.extent.YMax - (args.blocksize + args.y) * rasterlike.meanCellHeight)

    # Lower right coordinate of block (in cells)
    lx = min([args.x + args.blocksize, rasterlike.width])
    ly = min([args.y + args.blocksize, rasterlike.height])
    #   noting that (x, y) is the upper left coordinate (in cells)

    # Extract data block
    if raster is not None:
        myData = arcpy.RasterToNumPyArray(raster, arcpy.Point(mx, my),
                                          lx - args.x, ly - args.y, args.nodata)
    else:
        if args.dtypename == "int":
            dtype = int
        if args.dtypename == "float":
            dtype = float
        myData = numpy.empty([ly - args.y, lx - args.x], dtype)
        myData.fill(args.nodata)

    pickledict = open(args.pickledict, 'rb')
    dict = pickle.load(pickledict)

    for row in dict.keys():
        if row < ly and row >= args.y:
            for col in dict[row].keys():
                if col < lx and col >= args.x:
                    myData[row - args.y, col - args.x] = dict[row][col]

    # Convert data block back to raster
    myRasterBlock = arcpy.NumPyArrayToRaster(myData, arcpy.Point(mx, my),
                                             rasterlike.meanCellWidth,
                                             rasterlike.meanCellHeight, args.nodata)


    myRasterBlock.save(filetemp)


    # Release raster objects from memory
    del myRasterBlock
    del myData
