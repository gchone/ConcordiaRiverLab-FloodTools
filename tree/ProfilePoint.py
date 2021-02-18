# coding: latin-1

# Fichier ProfilePoint.py
# v0.0.2 - 24/10/2017

### Contenu ###
# classe ProfilePoint : Classe repr�sentant un point du profil longitudinal

### Historique des versions ###
# v0.0.1 - 28/09/2017 - Cr�ation - Gu�nol� Chon�
# v0.0.2 - 24/10/2017 - Description modifi�e - Gu�nol� Chon�
# v0.0.3 - 09/05/2019 - Pickle friendly - Gu�nol� Chon�
# v0.1 - Nov 2020 - Modification de la structure pour accommoder des profiles multiples

# Structure:
# ProfilePoint a des attributs (de type "z_bed", "width", "flow_acc", etc...) s'il est de type ProfilePoint
# Il a un dictionnaire (data_dict) de __ProfilePoint_data s'il est de type ProfilePointMulti
# Les cl�s de data_dict sont les noms des rasters (par journ�e d'acquisition LiDAR), les attributs de
#  __ProfilePoint_data sont de type "z_bed", "width", "flow_acc", etc...


import collections

class ProfilePoint(object):


    def __init__(self, segment, X, Y, dist, dictdata):
        #zlidar, width, n, Q:
        #   dist : float - distance (en m) jusqu'� la section aval
        #   zbed : float - elevation du lit (en m)
        #   width : float - largeur (en m)

        for key, elem in dictdata.items():
            self.__dict__[key] = elem

        self.segment = segment
        self.X = X
        self.Y = Y
        # dist = distance to downstream point
        self.dist=dist


class ProfilePoint_data(object):
    __slots__ = ["n", "Q", "z", "h", "width", "y", "s", "ws", "z_fill", "proxy_s", "ws_before_correction", "run_num", "dist", "wslidar", "dif", "idcorrection"]
    def __init__(self, dist, dictdata):
        self.dist = dist
        for key, elem in dictdata.items():
            setattr(self, key, elem)
            #self.__dict__[key] = elem



class ProfilePointMulti(ProfilePoint):
    __slots__ = ["X", "Y", "dist", "data_dict", "row", "col"]
    def __init__(self, X, Y, dist, dictdata):

        # zlidar, width, n, Q:
        #   dist : float - distance (en m) jusqu'� la section aval
        #   zbed : float - elevation du lit (en m)
        #   width : float - largeur (en m)

        self.data_dict = {}
        for raster_name, subdict in dictdata.items():
            # dist = distance to downstream point
            # passed to the __ProfilePoint_data, but kept in the ProfilePointMulti in read only
            self.data_dict[raster_name] = ProfilePoint_data(dist, subdict)

        self.X = X
        self.Y = Y

    def __setattr__(self, key, value):
        if key == "dist":
            for raster_name, PP_data in self.data_dict.items():
                PP_data.dist = value
        else:
            super(ProfilePointMulti, self).__setattr__(key, value)