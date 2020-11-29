# coding: latin-1

#####################################################
# Guénolé Choné
# Concordia University
# Geography, Planning and Environment Department
# guenole.chone@concordia.ca
#####################################################

# Versions
# v1.0 - Juillet 2018 - Création


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

    for tree in trees:
        pointup = None
        listtointerpol = []
        totaldistance = 0
        for segment, prev_cs, cs in tree.uptodown_browsepts():
            if cs.tointerpolate != valuesatcs.nodata:
                if pointup is not None:
                    totaldistance += cs.dist
                    interpolatetodown = True
                    if hasattr(cs, "lastinterpolatedupcs"):
                        # interpolation was already done, check if this one is better
                        interpolatetodown = abs(cs.lastinterpolatedupcs.tointerpolate - cs.tointerpolate) > abs(pointup.tointerpolate - cs.tointerpolate)

                    if interpolatetodown:
                        # interpolation
                        localdistance = 0
                        for csinlist in listtointerpol:
                            localdistance += prev_cs.dist
                            csinlist.interpolated = localdistance * (cs.tointerpolate - pointup.tointerpolate) / totaldistance + pointup.tointerpolate
                        cs.lastinterpolatedupcs = pointup
                    else:
                        # copy the upstream value until the confluence
                        for csinlist in listtointerpol:
                            if not hasattr(csinlist, "interpolated"):
                                csinlist.interpolated = pointup.tointerpolate
                else:
                    # copy the value at the upstream ends
                    for csinlist in listtointerpol:
                        csinlist.interpolated = cs.tointerpolate
                pointup = cs
                cs.interpolated = cs.tointerpolate
                lastvalue = cs.tointerpolate
                listtointerpol = []
                totaldistance = 0
            else:
                totaldistance += cs.dist
                listtointerpol.append(cs)

    # Saving the results
    Result = RasterIO(r_flowdir, str_results, float,-255)
    for segment in tree.treesegments():
        for pt in segment.get_profile():
            if hasattr(pt, "interpolated"):
                Result.setValue(pt.row, pt.col, pt.interpolated)
            else:
                #downstream end
                Result.setValue(pt.row, pt.col, lastvalue)
    Result.save()


    return



