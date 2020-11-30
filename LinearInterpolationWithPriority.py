# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Nov 2020 - Création


import arcpy
from RasterIO import *
from tree.OurTreeSegment import *
from tree.OurTreeManager import *





def execute_LinearInterpolationWithPriority(r_flowdir,  str_frompoint, r_values, str_results, messages, language="FR"):

    # Chargement des fichiers
    flowdir = RasterIO(r_flowdir)
    valuesatcs = RasterIO(r_values)
    try:
        flowdir.checkMatch(valuesatcs)
    except Exception as e:
        messages.addErrorMessage(e.message)

    trees = build_trees(flowdir, str_frompoint, tointerpolate=valuesatcs)

    # Find how to interpolate
    # Interpolation can not be done in this first run through the trees because the totaldistance must be calculated first
    for tree in trees:
        totaldistance = 0

        datacs_down = None
        for segment in tree.treesegments():
            for cs in segment.get_profile():
                if cs.tointerpolate != valuesatcs.nodata:
                    datacs_down = cs

                bestcsup = None
                for datacs_up in tree.points_up_with_data(segment, cs, "tointerpolate", valuesatcs.nodata):
                    if datacs_down is not None:
                        # a downstream point exists: looking for the upstream point with the closest value
                        if bestcsup is None or (abs(datacs_down.tointerpolate - datacs_up.tointerpolate) < abs(datacs_down.tointerpolate - bestcsup.tointerpolate)):
                            bestcsup = datacs_up
                    else:
                        # a downstream point does not exist: looking for the upstream point with the highest value
                        if bestcsup is None or (datacs_up.tointerpolate > bestcsup.tointerpolate):
                            bestcsup = datacs_up

                cs.datacs_up = bestcsup
                if (datacs_down is not None) and (datacs_down.datacs_up == cs.datacs_up):
                    # general case
                    cs.datacs_down = datacs_down
                else:
                    # special case at confluence, the local cs in a narrow steam, must be extrapolated from the upstream data
                    # Or, the cs is downstream the most downstream data point
                    cs.datacs_down = None

                totaldistance += cs.dist
                cs.totaldist = totaldistance


    # Calculating the interpolations and saving the results
    Result = RasterIO(r_values, str_results, float, -255)
    for tree in trees:
        for segment in tree.treesegments():
            for cs in segment.get_profile():
                if cs.datacs_down is None:
                    # extrapolation from upstream
                    cs.interpolated = cs.datacs_up.tointerpolate
                else:
                    if cs.datacs_up is None:
                        # extrapolation from downstream
                        cs.interpolated = cs.datacs_down.tointerpolate
                    else:
                        # interpolation
                        cs.interpolated = (cs.totaldist - cs.datacs_down.totaldist) \
                                          * (cs.datacs_up.tointerpolate - cs.datacs_down.tointerpolate) \
                                          / (cs.datacs_up.totaldist - cs.datacs_down.totaldist) \
                                          + cs.datacs_down.tointerpolate
                Result.setValue(cs.row, cs.col, cs.interpolated)




    Result.save()


    return



class Messages():
    def addErrorMessage(self, text):
        print(text)

    def addWarningMessage(self, text):
        print(text)

    def addMessage(self, text):
        print(text)

if __name__ == "__main__":
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True
    arcpy.env.scratchWorkspace = r"F:\MSP2\tmp"
    messages = Messages()

    flowdir = arcpy.Raster(r"D:\InfoCrue\Bécancour\Width\G_Width_et_VerifThiessen\d4fd")
    frompoints = r"D:\InfoCrue\Bécancour\Width\G_Width_et_VerifThiessen\dep_pts.shp"
    widthpts = arcpy.Raster(r"D:\InfoCrue\Bécancour\Width\G_Width_et_VerifThiessen\points_width\mnt_12_04_29")
    output = r"D:\InfoCrue\tmp\interw04_29f"

    execute_LinearInterpolationWithPriority(flowdir, frompoints, widthpts, output, messages)