# -*- coding: utf-8 -*-

### Historique des versions ###
# v1.0 - Mars 2021 - Création - Guénolé Choné

import arcpy
import os

class _GarbageManager(object):

    __instance = None
    __garbagelist = []

    @staticmethod
    def getInstance():
        """ Static access method. """
        if _GarbageManager.__instance == None:
            _GarbageManager()
        return _GarbageManager.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if _GarbageManager.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            _GarbageManager.__instance = self

    def add_to_garbagebin(self, path):
        self.__garbagelist.append(path)

    def empty_garbagebin(self):
        for item in self.__garbagelist:
            if arcpy.Exists(item):
                arcpy.Delete_management(item)
        self.__garbagelist = []

def CleanTempFiles():
    gb = _GarbageManager.getInstance()
    gb.empty_garbagebin()

def AddToGarbageBin(item):
    gb = _GarbageManager.getInstance()
    gb.add_to_garbagebin(item)
