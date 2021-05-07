# -*- coding: utf-8 -*-

from tree.RiverNetwork import *
from BedAssessmentDirectLinearNet import *


# This class replace de Arcpy Messages class avalaible when using a tool from ArcGIS
# It here so we can use the tools from Python (not from the ArcGIS interface)
class Messages():
    def addErrorMessage(self, text):
        print (text)

    def addWarningMessage(self, text):
        print (text)

    def addMessage(self, text):
        print (text)


if __name__ == "__main__":

    messages = Messages()
    arcpy.env.overwriteOutput = True

    # Input data
    route = r"E:\InfoCrue\Refontebathy\SyntheticInputs\route.shp"
    routelinks = r"E:\InfoCrue\Refontebathy\SyntheticInputs\routelinks.dbf"
    # Output data
    points1 = r"E:\InfoCrue\Refontebathy\SyntheticInputs\memorytest\data5.dbf"
    createtable = r"E:\InfoCrue\Refontebathy\SyntheticInputs\memorytest\solverdata5c.dbf"

    ### Loading data ###
    # Loading the network
    RiverNetwork.dict_attr_fields['id'] = "Id"
    rivernet = RiverNetwork(route, routelinks)
    # Loading the points on the network
    Points_collection.dict_attr_fields['dist'] = 'dist2'
    Points_collection.dict_attr_fields['offset'] = 'offset'
    new_dict_attr_field = {"wslidar": "ws",
                           "Q": "q",
                           "width": "w"
                           }
    rivernet.add_points_collection(points1, new_dict_attr_field, "data")

    # Executing the bed assessment
    execute_BedAssessment(rivernet, rivernet.points_collection["data"], 0.03, 0.0001, messages)

    # Saving results
    dict_attr_field = {"id": "ORIG_ID",
                       "z": "bed_elev",
                       }
    rivernet.points_collection["data"].save_points(createtable,dict_attr_field)







