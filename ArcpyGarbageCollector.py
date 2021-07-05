# -*- coding: utf-8 -*-


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
            self.inmemoryindex = 0

    def add_to_garbagebin(self, path):
        self.__garbagelist.append(path)

    def empty_garbagebin(self):
        for item in self.__garbagelist:
            if arcpy.Exists(item):
                arcpy.Delete_management(item)
        self.__garbagelist = []

    def remove(self, item):
        if item in self.__garbagelist:
            if arcpy.Exists(item):
                arcpy.Delete_management(item)
            self.__garbagelist.remove(item)

def CreateScratchName(prefix, data_type, workspace):
    # "ArcInfoTable" doesn't work for creating tables with arcpy.CreateScratchName in gdb. This function allow it.
    # Also, in memory object to not receive an unique id
    if workspace=="in_memory":
        gb = _GarbageManager.getInstance()
        gb.inmemoryindex += 1
        return arcpy.CreateScratchName(prefix+str(gb.inmemoryindex), data_type=data_type, workspace=workspace)
    else:
        if data_type == "ArcInfoTable" or data_type == "FeatureClass":
            if arcpy.Describe(workspace).dataType == "Workspace":
                # In a Geodatabase, tables name should be created with data_type == "FeatureClass"
                name = arcpy.CreateScratchName(prefix, data_type="FeatureClass", workspace=workspace)
            else: #arcpy.Describe(workspace).dataType == "Folder"
                name = arcpy.CreateScratchName(prefix, data_type=data_type, workspace=workspace)
        AddToGarbageBin(name)
        return name
            # tablecsn = arcpy.CreateScratchName(prefix, data_type="ArcInfoTable", workspace=workspace)
            # featurecsn = arcpy.CreateScratchName(prefix, data_type="FeatureClass", workspace=workspace)
            # tablename = os.path.splitext(os.path.basename(tablecsn))[0] # splittext( )[0] is for retrieving only the file name if there is an extension
            # featurename = os.path.splitext(os.path.basename(featurecsn))[0]
            # if len(tablename) > len(featurename):
            #     selectedname = tablename
            # elif len(tablename) < len(featurename):
            #     selectedname = featurename
            # else:
            #     selectedname = max(tablename, featurename)
            #
            # if data_type == "ArcInfoTable":
            #     # In addition, there are some issues with tables without extension in folders. It's better to use dbf tables
            #     return os.path.join(workspace, selectedname+".dbf")
            # else:
            #     return os.path.join(workspace, selectedname + ".shp")




def CleanAllTempFiles():
    gb = _GarbageManager.getInstance()
    gb.empty_garbagebin()

def CleanTempFile(file):
    gb = _GarbageManager.getInstance()
    gb.remove(file)

def AddToGarbageBin(item):
    gb = _GarbageManager.getInstance()
    gb.add_to_garbagebin(item)
