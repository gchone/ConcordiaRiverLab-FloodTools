# coding: latin-1

# Fichier ProfilePoint.py
# v0.0.2 - 24/10/2017

### Contenu ###
# classe ProfilePoint : Classe repr�sentant un point du profil longitudinal

### Historique des versions ###
# v0.0.1 - 28/09/2017 - Cr�ation - Gu�nol� Chon�
# v0.0.2 - 24/10/2017 - Description modifi�e - Gu�nol� Chon�
# v0.0.3 - 09/05/2019 - Pickle friendly - Gu�nol� Chon�



class ProfilePoint(object):
    def __init__(self, row, col, dist, dictdata):
        #zlidar, width, n, Q:
        #   dist : float - distance (en m) jusqu'� la section aval
        #   zbed : float - elevation du lit (en m)
        #   width : float - largeur (en m)
        #self.data = dictdata
        for key, elem in dictdata.items():
            self.__dict__[key] = elem
        self.row = row
        self.col = col
        # dist = distance to downstream point
        self.dist=dist

    # def __setattr__(self, key, value):
    #     if key in self.data:
    #         self.data[key] == value
    #     else:
    #         super(ProfilePoint, self).__setattr__(key, value)
    #
    # def __getattr__(self, name, ):
    #     if name in self.data:
    #         return self.data[name]
    #     else:
    #         raise AttributeError
    #         return None
    #
    # def __setstate__(self, state):
    #     self.__dict__ = state
    #
    # def __getstate__(self):
    #     return self.__dict__
