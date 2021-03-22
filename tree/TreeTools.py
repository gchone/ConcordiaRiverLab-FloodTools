# -*- coding: utf-8 -*-

### Historique des versions ###
# v1.0 - Jan 2021 - Création - Guénolé Choné

# ArcGIS tools for tree manipulation


from tree.RiverNetwork import *
from RasterIO import *
import ArcpyGarbageCollector as gc

def execute_TreeFromFlowDir(r_flowdir, str_frompoints, str_output_routes, routeID_field, str_output_points, messages):
    """
    Create a tree structure following the Flow Direction from the From points.

    :param r_flowdir:
    :param str_frompoints:
    :param str_output_routes:
    :param str_output_points:
    :return:
    """
    flowdir = RasterIO(r_flowdir)
    trees = []
    segmentid = 0

    treated_pts = {}

    class tmp_ProfilePoint(object):
        pass

    # Traitement effectué pour chaque point de départ
    frompointcursor = arcpy.da.SearchCursor(str_frompoints, ["SHAPE@", "OID@"])
    for frompoint in frompointcursor:

        # On prend l'objet géométrique (le point) associé à la ligne dans la table
        frompointshape = frompoint[0].firstPoint

        # Conversion des coordonnées
        currentcol = flowdir.XtoCol(frompointshape.X)
        currentrow = flowdir.YtoRow(frompointshape.Y)

        # Tests de sécurité pour s'assurer que le point de départ est à l'intérieurs des rasters
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
        newtreeseg = TreeSegment(segmentid)
        newtreeseg.__ptsprofile = []


        # Traitement effectué sur chaque cellule le long de l'écoulement
        while (intheraster):

            ptprofile = tmp_ProfilePoint()

            ptprofile.X = flowdir.ColtoX(currentcol)
            ptprofile.Y = flowdir.RowtoY(currentrow)
            ptprofile.row = currentrow
            ptprofile.col = currentcol

            newtreeseg.__ptsprofile.insert(0, ptprofile)
            treated_pts[(currentrow, currentcol)] = newtreeseg

            # On cherche le prochain point à partir du flow direction
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



            # Tests de sécurité pour s'assurer que l'on ne sorte pas des rasters
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
                ptprofile.dist = currentdistance
                if (currentrow, currentcol) in treated_pts:
                    # Atteinte d'un confluent
                    intheraster = False
                    segmentid += 1
                    # on cherche l'arbre et le segment que l'on vient de rejoindre
                    oldsegment = treated_pts[(currentrow, currentcol)]

                    # fork
                    newchild = TreeSegment(segmentid)
                    childrenlist = []
                    for child in oldsegment.get_childrens():
                        childrenlist.append(child)
                    for child in childrenlist:
                        oldsegment.remove_child(child)
                        newchild.add_child(child)
                    oldsegment.add_child(newchild)
                    oldsegment.add_child(newtreeseg)

                    for i in range(len(oldsegment.__ptsprofile)):
                        pt = oldsegment.__ptsprofile[i]
                        if pt.row == currentrow and pt.col == currentcol:
                           break
                    newchild.__ptsprofile = oldsegment.__ptsprofile[i + 1:]
                    oldsegment.__ptsprofile = oldsegment.__ptsprofile[:i + 1]


            else:
                ptprofile.dist = 0
                tree = Tree()
                tree.treeroot = newtreeseg
                trees.append(tree)

    arcpy.CreateFeatureclass_management(os.path.dirname(str_output_points),
                                        os.path.basename(str_output_points), "POINT", spatial_reference=r_flowdir)

    arcpy.AddField_management(str_output_points, "dist", "FLOAT")
    arcpy.AddField_management(str_output_points, routeID_field, "LONG")
    pointcursor = arcpy.da.InsertCursor(str_output_points, ["SHAPE@XY", "dist", routeID_field])

    arcpy.CreateFeatureclass_management("in_memory", "LINES", "POLYLINE", spatial_reference=r_flowdir)
    lines = "in_memory\LINES"

    arcpy.AddField_management(lines, routeID_field, "LONG")
    linecursor = arcpy.da.InsertCursor(lines, ["SHAPE@", routeID_field])
    for tree in trees:
        for segment in tree.treesegments():
            totaldist = 0
            vertices = arcpy.Array()
            if not segment.is_root():
                # les lignes commencent au dernier point du segment précédent
                vertices.add(arcpy.Point(segment.get_parent().__ptsprofile[-1].X, segment.get_parent().__ptsprofile[-1].Y))
            for pt in segment.__ptsprofile:
                totaldist += pt.dist
                pointcursor.insertRow([(pt.X, pt.Y), totaldist, segment.id])
                vertices.add(arcpy.Point(pt.X, pt.Y))
            line = arcpy.Polyline(vertices)
            linecursor.insertRow([line, segment.id])

    # Create routes from start point to end point
    arcpy.AddField_management(lines, routeID_field, "LONG")
    arcpy.AddField_management(lines, "FromF", "FLOAT")
    arcpy.CalculateField_management(lines, "FromF", "0", "PYTHON")
    arcpy.AddGeometryAttributes_management(lines, "LENGTH_GEODESIC")
    arcpy.CreateRoutes_lr(lines, routeID_field, str_output_routes, "TWO_FIELDS", from_measure_field="FromF",
                          to_measure_field="LENGTH_GEO")
    arcpy.AddGeometryAttributes_management(str_output_routes, "LENGTH_GEODESIC")



def __recursivebuildtree(downstream_junction, np_junctions, np_net, netid_name, linkcursor):

    if downstream_junction["ENDTYPE"] == "End":
        # The line should be flipped
        expression =  netid_name + " = " + str(downstream_junction["ORIG_FID"])
        arcpy.SelectLayerByAttribute_management("netlyr", "ADD_TO_SELECTION", expression)

    # Find the upstream junction for the current reach
    condition1 = np_junctions["ORIG_FID"] == downstream_junction["ORIG_FID"]
    condition2 = np_junctions["FEAT_SEQ"] <> downstream_junction["FEAT_SEQ"]
    current_upstream_junction = np.extract(np.logical_and(condition1, condition2), np_junctions)[0]

    # Find other junctions at the same place
    condition1 = np_junctions["FEAT_SEQ"] == current_upstream_junction["FEAT_SEQ"]
    condition2 = np_junctions["ORIG_FID"] <> current_upstream_junction["ORIG_FID"]

    other_upstream_junctions = np.extract(np.logical_and(condition1, condition2), np_junctions)

    for upstream_junction in other_upstream_junctions:
            # Add a row in the links table
            linkcursor.insertRow([downstream_junction["ORIG_FID"],upstream_junction["ORIG_FID"]])
            # Apply recursively
            __recursivebuildtree(downstream_junction, np_junctions, np_net, netid_name, linkcursor)

    return



def execute_CreateTreeFromShapefile(rivernet, route_shapefile, routelinks_table, routeID_field, downstream_reach_field):

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
        arcpy.AddField_management(rivernetcopy, RiverNetwork.reaches_linkfielddown, "LONG")
        arcpy.AddField_management(rivernetcopy, RiverNetwork.reaches_linkfieldup, "LONG")
        linkcursor = arcpy.da.InsertCursor(rivernetcopy, [RiverNetwork.reaches_linkfielddown, RiverNetwork.reaches_linkfieldup])

        for downstream_junction in downstream_junctions:
            __recursivebuildtree(downstream_junction, np_junctions, np_net, arcpy.Describe(rivernetcopy).OIDFieldName, linkcursor)

        # Flip the wrongly orientated lines
        arcpy.FlipLine_edit("netlyr")
        # Create routes from start point to end point
        arcpy.AddField_management(rivernetcopy, routeID_field, "LONG")
        arcpy.CalculateField_management(rivernetcopy, routeID_field, "!" + netid_name + "!", "PYTHON")
        arcpy.AddField_management(rivernetcopy, "FromF", "FLOAT")
        arcpy.CalculateField_management(rivernetcopy, "FromF", "0", "PYTHON")
        arcpy.AddGeometryAttributes_management(rivernetcopy, "LENGTH")
        arcpy.CreateRoutes_lr(rivernetcopy, routeID_field, route_shapefile, "TWO_FIELDS", from_measure_field="FromF",
                              to_measure_field="LENGTH")

        arcpy.DeleteField_management(route_shapefile, ["FromF"])
        arcpy.DeleteField_management(route_shapefile, ["LENGTH"])
    finally:
        gc.CleanTempFiles()







