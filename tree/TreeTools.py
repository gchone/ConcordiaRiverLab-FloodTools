# -*- coding: utf-8 -*-


# ArcGIS tools for tree manipulation


from tree.RiverNetwork import *
from RasterIO import *
import ArcpyGarbageCollector as gc

def execute_TreeFromFlowDir(r_flowdir, str_frompoints, route_shapefile, routelinks_table, routeID_field, str_output_points, messages):
    """
    Create a tree structure following the Flow Direction from the From points.

    :param r_flowdir:
    :param str_frompoints:
    :param str_output_routes:
    :param str_output_points:
    :return:
    """



    flowdir = RasterIO(r_flowdir)

    segmentid = 0
    pointid = 0

    # create the links table as a numpy array
    links = np.empty(0, dtype=[(RiverNetwork.reaches_linkfielddown, 'i4'), (RiverNetwork.reaches_linkfieldup, 'i4')])

    # For efficiency, the points table is managed as a numpy array (and latter converted into a table)
    pointstype = [("id", 'i4'), ("RID", 'i4'), ("dist", 'f4'), ("offset", 'f4'), ("X", 'f8'), ("Y", 'f8'), ("row", 'i4'), ("col", 'i4')]
    pointsarray = np.empty(0, dtype=pointstype)

    # this dict is used to stored the point downstream of each reach (first point to use when building the river lines)
    initialpoint = {}

    # Starting at each From point
    frompointcursor = arcpy.da.SearchCursor(str_frompoints, ["SHAPE@", "OID@"])
    for frompoint in frompointcursor:

        # Point Shape
        frompointshape = frompoint[0].firstPoint

        # Converting coordinates
        currentcol = flowdir.XtoCol(frompointshape.X)
        currentrow = flowdir.YtoRow(frompointshape.Y)

        # Security check to make sure the From point is inside the Flow dir raster
        intheraster = True
        if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
            intheraster = False
        elif (flowdir.getValue(currentrow, currentcol) != 1 and flowdir.getValue(currentrow, currentcol) != 2 and
                      flowdir.getValue(currentrow, currentcol) != 4 and flowdir.getValue(currentrow,
                                                                                         currentcol) != 8 and
                      flowdir.getValue(currentrow, currentcol) != 16 and flowdir.getValue(currentrow,
                                                                                          currentcol) != 32 and flowdir.getValue(
            currentrow, currentcol) != 64 and flowdir.getValue(currentrow, currentcol) != 128):
            intheraster = False

        segmentid += 1
        totaldist = 0

        # For efficiency, points are only added to the pointsarray by batch. They are temporary stored as a list of list
        #  witch each point is formatted as a list [id, RID, dist, offset, X, Y, row, column]
        pointslist = []

        # For each point encountered along the flow path
        while (intheraster):

            # Add the point to the list
            pointid += 1
            pointslist.append([pointid, segmentid, totaldist, 0, flowdir.ColtoX(currentcol), flowdir.RowtoY(currentrow), currentrow, currentcol])

            # Look for the next point
            direction = flowdir.getValue(currentrow, currentcol)
            if (direction == 1):
                currentcol = currentcol + 1
                currentdistance = flowdir.raster.meanCellWidth
            if (direction == 2):
                currentcol = currentcol + 1
                currentrow = currentrow + 1
                currentdistance = math.sqrt(
                    flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)
            if (direction == 4):
                currentrow = currentrow + 1
                currentdistance = flowdir.raster.meanCellHeight
            if (direction == 8):
                currentcol = currentcol - 1
                currentrow = currentrow + 1
                currentdistance = math.sqrt(
                    flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)
            if (direction == 16):
                currentcol = currentcol - 1
                currentdistance = flowdir.raster.meanCellWidth
            if (direction == 32):
                currentcol = currentcol - 1
                currentrow = currentrow - 1
                currentdistance = math.sqrt(
                    flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)
            if (direction == 64):
                currentrow = currentrow - 1
                currentdistance = flowdir.raster.meanCellHeight
            if (direction == 128):
                currentcol = currentcol + 1
                currentrow = currentrow - 1
                currentdistance = math.sqrt(
                    flowdir.raster.meanCellWidth * flowdir.raster.meanCellWidth + flowdir.raster.meanCellHeight * flowdir.raster.meanCellHeight)



            # Security check to make sure the point is still inside the Flow dir raster
            if currentcol < 0 or currentcol >= flowdir.raster.width or currentrow < 0 or currentrow >= flowdir.raster.height:
                intheraster = False
            elif (flowdir.getValue(currentrow, currentcol) != 1 and flowdir.getValue(currentrow,
                                                                                     currentcol) != 2 and
                          flowdir.getValue(currentrow, currentcol) != 4 and flowdir.getValue(currentrow,
                                                                                             currentcol) != 8 and
                          flowdir.getValue(currentrow, currentcol) != 16 and flowdir.getValue(currentrow,
                                                                                              currentcol) != 32 and flowdir.getValue(
                currentrow, currentcol) != 64 and flowdir.getValue(currentrow, currentcol) != 128):
                intheraster = False

            if intheraster:
                totaldist += currentdistance

                # Check if the new points coordinates (in row, column) are already in the points numpy array
                checkrow = pointsarray["row"] == currentrow
                checkcol = pointsarray["col"] == currentcol
                checkpoint = np.extract(np.logical_and(checkrow, checkcol), pointsarray)

                if len(checkpoint) > 0:

                    confluencepoint = checkpoint[0]
                    # A confluence with a previously treated flow path is met
                    # The reach that is met is split in two
                    # A new RID is assigned to the upstream part of this reach
                    matchingrid = pointsarray["RID"] == confluencepoint["RID"]
                    matchingdist = pointsarray["dist"] > confluencepoint["dist"]
                    pointsarray["RID"][np.logical_and(matchingrid, matchingdist)] = segmentid + 1

                    # The link table need to be updated too (new RID for the upstream part of the met reach)
                    links[RiverNetwork.reaches_linkfielddown][links[RiverNetwork.reaches_linkfielddown] == confluencepoint["RID"]] = segmentid + 1

                    # Adding the pointslist to the pointsarray
                    #   but first, the distance value must be reverse (it was computed backward. It must be from downstream to upstream), and the points must be tuples
                    pointslisttuple = []
                    for point in pointslist:
                        pointslisttuple.append((point[0], point[1], totaldist - point[2], point[3], point[4], point[5], point[6], point[7]))

                    pointsarray = np.append(pointsarray, np.array(pointslisttuple, dtype=pointstype))

                    # Adding the confluence info in the link table
                    to_add = numpy.empty(2, dtype=links.dtype)
                    to_add[RiverNetwork.reaches_linkfielddown] = confluencepoint["RID"]
                    to_add[RiverNetwork.reaches_linkfieldup][0] = segmentid
                    to_add[RiverNetwork.reaches_linkfieldup][1] = segmentid + 1
                    links = numpy.append(links, to_add)

                    # Storing the downstream point of the upstream reach
                    initialpoint[segmentid] = arcpy.Point(float(confluencepoint["X"]), float(confluencepoint["Y"]))
                    initialpoint[segmentid + 1] = arcpy.Point(float(confluencepoint["X"]), float(confluencepoint["Y"]))

                    segmentid += 1
                    intheraster = False
            else:
                # Adding the pointslist to the pointsarray
                #   but first, the distance value must be reverse (it was computed backward. It must be from downstream to upstream), and the points must be tuples
                pointslisttuple = []
                for point in pointslist:
                    pointslisttuple.append((point[0], point[1], totaldist - point[2], point[3], point[4], point[5], point[6], point[7]))
                pointsarray = np.append(pointsarray, np.array(pointslisttuple, dtype=pointstype))

    # Saving the links
    if arcpy.Exists(routelinks_table) and arcpy.env.overwriteOutput == True:
        arcpy.Delete_management(routelinks_table)
    arcpy.da.NumPyArrayToTable(links, routelinks_table)

    # Saving the points
    if arcpy.Exists(str_output_points) and arcpy.env.overwriteOutput == True:
        arcpy.Delete_management(str_output_points)
    arcpy.da.NumPyArrayToTable(pointsarray, str_output_points)

    # Creating lines
    arcpy.CreateFeatureclass_management("in_memory", "LINES", "POLYLINE", spatial_reference=r_flowdir)
    lines = "in_memory\LINES"
    arcpy.AddField_management(lines, routeID_field, "LONG")
    linecursor = arcpy.da.InsertCursor(lines, ["SHAPE@", routeID_field])
    reachidlist = set(pointsarray["RID"])
    for reachid in reachidlist:
        # New line
        vertices = arcpy.Array()
        points = np.sort(pointsarray[pointsarray["RID"] == reachid], order="dist")
        # Add the downstream point if it exists
        if reachid in initialpoint.keys():
            vertices.add(initialpoint[reachid])
        for point in points:
            vertices.add(arcpy.Point(float(point["X"]), float(point["Y"])))
        line = arcpy.Polyline(vertices)
        linecursor.insertRow([line, reachid])

    # Create routes from start point to end point
    arcpy.AddField_management(lines, routeID_field, "LONG")
    arcpy.AddField_management(lines, "FromF", "FLOAT")
    if arcpy.Describe(arcpy.env.scratchWorkspace).dataType=="Folder":
        # if the scrach workspace is a folder, the copy of the river network is a shapefile (else, it's within a
        # File geodatabase and already has a Length field)
        arcpy.CalculateField_management(lines, "FromF", "0", "PYTHON")
        #arcpy.AddGeometryAttributes_management(rivernetcopy, "LENGTH") # "LENGTH" is not an available option and I can't get why
        arcpy.AddField_management(lines, "LENGTH", "DOUBLE")
        arcpy.CalculateField_management(lines, "LENGTH", "!shape.length!", "PYTHON")
        Lengthfield = "LENGTH"
    else:
        Lengthfield = "SHAPE_LENGTH"
    arcpy.CreateRoutes_lr(lines, routeID_field, route_shapefile, "TWO_FIELDS",
                             from_measure_field="FromF",
                             to_measure_field=Lengthfield)





def execute_CreateTreeFromShapefile(rivernet, route_shapefile, routelinks_table, routeID_field, downstream_reach_field):

    def __recursivebuildtree(downstream_junction, np_junctions, np_net, netid_name, linkcursor):

        if downstream_junction["ENDTYPE"] == "End":
            # The line should be flipped
            expression = netid_name + " = " + str(downstream_junction["ORIG_FID"])
            arcpy.SelectLayerByAttribute_management("netlyr", "ADD_TO_SELECTION", expression)

        # Find the upstream junction for the current reach
        condition1 = np_junctions["ORIG_FID"] == downstream_junction["ORIG_FID"]
        condition2 = np_junctions["FEAT_SEQ"] != downstream_junction["FEAT_SEQ"]
        current_upstream_junction = np.extract(np.logical_and(condition1, condition2), np_junctions)[0]

        # Find other junctions at the same place
        condition1 = np_junctions["FEAT_SEQ"] == current_upstream_junction["FEAT_SEQ"]
        condition2 = np_junctions["ORIG_FID"] != current_upstream_junction["ORIG_FID"]

        other_upstream_junctions = np.extract(np.logical_and(condition1, condition2), np_junctions)

        for upstream_junction in other_upstream_junctions:
            # Add a row in the links table
            linkcursor.insertRow([downstream_junction["ORIG_FID"], upstream_junction["ORIG_FID"]])
            # Apply recursively
            __recursivebuildtree(upstream_junction, np_junctions, np_net, netid_name, linkcursor)

        return


    try:

        # Create Junction points: two points created by reach, at both end of the line
        # (done separately with "END" and "START", rather than with "BOTH_ENDS", to keep track of what point is at which extremity)
        with arcpy.EnvManager(outputMFlag="Disabled"):
            with arcpy.EnvManager(outputZFlag="Disabled"):
                # Do not included Z and M values in the points, as it will mess with the grouping by Shape step (it should only be based on X and Y position)
                junctions_end = gc.CreateScratchName("net", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
                arcpy.FeatureVerticesToPoints_management(rivernet, junctions_end, "END")
                junctions_start = gc.CreateScratchName("net", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
                arcpy.FeatureVerticesToPoints_management(rivernet, junctions_start, "START")
        arcpy.AddField_management(junctions_end, "ENDTYPE", "TEXT", field_length=10)
        arcpy.AddField_management(junctions_start, "ENDTYPE", "TEXT", field_length=10)
        arcpy.CalculateField_management(junctions_end, "ENDTYPE", "'End'", "PYTHON")
        arcpy.CalculateField_management(junctions_start, "ENDTYPE", "'Start'", "PYTHON")
        junctions = gc.CreateScratchName("net", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
        arcpy.Merge_management([junctions_end, junctions_start], junctions)
        junctionid_name = arcpy.Describe(junctions).OIDFieldName

        #   Add a id ("FEAT_SEQ") to the junction grouping junctions at the same place (same place = same id))
        junctions_table = gc.CreateScratchName("net", data_type="ArcInfoTable", workspace=arcpy.env.scratchWorkspace)
        arcpy.FindIdentical_management(junctions, junctions_table, ["Shape"])
        arcpy.JoinField_management(junctions, junctionid_name, junctions_table, "IN_FID")
        np_junctions = arcpy.da.FeatureClassToNumPyArray(junctions, [junctionid_name, "ORIG_FID", "FEAT_SEQ", "ENDTYPE"])

        # Find downstream ends
        # count the number of junctions at the same place
        u, indices, count = np.unique(np_junctions["FEAT_SEQ"], return_index=True, return_counts=True)
        # select only the ones with one junction only
        condition = np.array([item in u[count == 1] for item in np_junctions["FEAT_SEQ"]])

        # get a list of id of downstream reaches
        netid_name = arcpy.Describe(rivernet).OIDFieldName
        np_net = arcpy.da.FeatureClassToNumPyArray(rivernet, [netid_name, downstream_reach_field])
        net_down_id = np.extract(np_net[downstream_reach_field] == 1, np_net)[netid_name]
        # select only the junction from this list
        condition2 = np.array([item in net_down_id for item in np_junctions["ORIG_FID"]])

        downstream_junctions = np.extract(np.logical_and(condition, condition2), np_junctions)

        # Make a layer from a copy of the feature class (used for flipping lines)
        rivernetcopy = gc.CreateScratchName("net", data_type="FeatureClass", workspace=arcpy.env.scratchWorkspace)
        arcpy.CopyFeatures_management(rivernet, rivernetcopy)
        arcpy.MakeFeatureLayer_management(rivernetcopy, "netlyr")
        arcpy.SelectLayerByAttribute_management("netlyr", "CLEAR_SELECTION")

        # create the links table
        if arcpy.Exists(routelinks_table) and arcpy.env.overwriteOutput == True:
            arcpy.Delete_management(routelinks_table)
        arcpy.CreateTable_management(os.path.dirname(routelinks_table), os.path.basename(routelinks_table))
        arcpy.AddField_management(routelinks_table, RiverNetwork.reaches_linkfielddown, "LONG")
        arcpy.AddField_management(routelinks_table, RiverNetwork.reaches_linkfieldup, "LONG")
        if arcpy.Describe(os.path.dirname(routelinks_table)).dataType == "Folder":
            # ArcGIS create a "Field1" field by default for tables in folder
            arcpy.DeleteField_management(routelinks_table, "Field1")

        linkcursor = arcpy.da.InsertCursor(routelinks_table, [RiverNetwork.reaches_linkfielddown, RiverNetwork.reaches_linkfieldup])

        netcopyid_name = arcpy.Describe(rivernetcopy).OIDFieldName
        for downstream_junction in downstream_junctions:
            __recursivebuildtree(downstream_junction, np_junctions, np_net, netcopyid_name, linkcursor)

        # Flip the wrongly orientated lines
        arcpy.FlipLine_edit("netlyr")

        # Create routes from start point to end point

        arcpy.AddField_management(rivernetcopy, routeID_field, "LONG")
        arcpy.CalculateField_management(rivernetcopy, routeID_field, "!" + netcopyid_name + "!", "PYTHON")
        arcpy.AddField_management(rivernetcopy, "FromF", "FLOAT")

        if arcpy.Describe(arcpy.env.scratchWorkspace).dataType=="Folder":
            # if the scrach workspace is a folder, the copy of the river network is a shapefile (else, it's within a
            # File geodatabase and already has a Length field)
            arcpy.CalculateField_management(rivernetcopy, "FromF", "0", "PYTHON")
            #arcpy.AddGeometryAttributes_management(rivernetcopy, "LENGTH") # "LENGTH" is not an available option and I can't get why
            arcpy.AddField_management(rivernetcopy, "LENGTH", "DOUBLE")
            arcpy.CalculateField_management(rivernetcopy, "LENGTH", "!shape.length!", "PYTHON")
            #arcpy.CalculateGeometryAttributes_management(rivernetcopy, [["LENGTH", "LENGTH"]])
            Lengthfield = "LENGTH"
        else:
            Lengthfield = "SHAPE_LENGTH"
        arcpy.CreateRoutes_lr(rivernetcopy, routeID_field, route_shapefile, "TWO_FIELDS",
                                 from_measure_field="FromF",
                                 to_measure_field=Lengthfield)



    finally:
        gc.CleanTempFiles()








