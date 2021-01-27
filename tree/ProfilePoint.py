# -*- coding: utf-8 -*-

# Fichier ProfilePoint.py
# v0.0.2 - 24/10/2017

### Contenu ###
# classe ProfilePoint : Classe représentant un point du profil longitudinal

### Historique des versions ###
# v0.0.1 - 28/09/2017 - Création - Guénolé Choné
# v0.0.2 - 24/10/2017 - Description modifiée - Guénolé Choné
# v0.0.3 - 09/05/2019 - Pickle friendly - Guénolé Choné
# v0.1 - Nov 2020 - Modification de la structure pour accommoder des profiles multiples

# Structure:
# ProfilePoint a des attributs (de type "z_bed", "width", "flow_acc", etc...) s'il est de type ProfilePoint
# Il a un dictionnaire (data_dict) de __ProfilePoint_data s'il est de type ProfilePointMulti
# Les clés de data_dict sont les noms des rasters (par journée d'acquisition LiDAR), les attributs de
#  __ProfilePoint_data sont de type "z_bed", "width", "flow_acc", etc...



class ProfilePoint(object):

    def __init__(self, dataobj, dataobj_id):
        self.__dataobj = dataobj
        self.id = dataobj_id

    def __getattr__(self, key):
        return self.__dataobj.get_item(self.id, key)


