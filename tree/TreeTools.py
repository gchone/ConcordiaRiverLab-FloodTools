# -*- coding: utf-8 -*-

### Historique des versions ###
# v1.0 - Jan 2021 - Création - Guénolé Choné

# ArcGIS tools for tree manipulation


from tree.OurTreeManager import *
from RasterIO import *

def load_trees_from_FlowDir(r_flowdir, str_frompoints):
    flowdir = RasterIO(r_flowdir)
    trees = []
    segmentid = 0

    treated_pts = {}

    #class tmp_ProfilePoint(object):
    #   pass

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
        newtreeseg = OurTreeSegment(segmentid)

        # Traitement effectué sur chaque cellule le long de l'écoulement
        while (intheraster):

            ptprofile = ProfilePoint.ProfilePoint(newtreeseg, flowdir.ColtoX(currentcol), flowdir.RowtoY(currentrow), 0, {})

            #ptprofile.X = flowdir.ColtoX(currentcol)
            #ptprofile.Y = flowdir.RowtoY(currentrow)
            ptprofile.row = currentrow
            ptprofile.col = currentcol


            treated_pts[(currentrow, currentcol)] = ptprofile
            newtreeseg.get_profile().insert(0, ptprofile)

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
                    existingpt = treated_pts[(currentrow, currentcol)]
                    # Atteinte d'un confluent
                    intheraster = False
                    segmentid += 1
                    # on cherche l'arbre et le segment que l'on vient de rejoindre
                    #oldsegment = treated_pts[(currentrow, currentcol)]
                    oldsegment = existingpt.segment

                    # fork
                    newchild = OurTreeSegment(segmentid)
                    childrenlist = []
                    for child in oldsegment.get_childrens():
                        childrenlist.append(child)
                    for child in childrenlist:
                        oldsegment.remove_child(child)
                        newchild.add_child(child)
                    oldsegment.add_child(newchild)
                    oldsegment.add_child(newtreeseg)

                    for i in range(len(oldsegment.get_profile())):
                        pt = oldsegment.get_profile()[i]
                        if pt.row == currentrow and pt.col == currentcol:
                            break
                    newchild.set_profile(oldsegment.get_profile()[i + 1:])
                    oldsegment.set_profile(oldsegment.get_profile()[:i + 1])
                    for pt in newchild.get_profile():
                        pt.segment = newchild





            else:
                ptprofile.dist = 0
                tree = OurTreeManager()
                tree.treeroot = newtreeseg
                trees.append(tree)


    return trees

def execute_TreeFromFlowDir(r_flowdir, str_frompoints, str_output_routes, routeID_field, str_output_points, messages):
    """
    Create a tree structure following the Flow Direction from the From points.


    """

    trees = load_trees_from_FlowDir(r_flowdir, str_frompoints)

    arcpy.CreateFeatureclass_management(os.path.dirname(str_output_points),
                                        os.path.basename(str_output_points), "POINT", spatial_reference=r_flowdir)

    arcpy.AddField_management(str_output_points, "dist", "FLOAT")
    arcpy.AddField_management(str_output_points, "totald", "FLOAT")
    arcpy.AddField_management(str_output_points, routeID_field, "LONG")
    pointcursor = arcpy.da.InsertCursor(str_output_points, ["SHAPE@XY", "dist", "totald", routeID_field])

    arcpy.CreateFeatureclass_management("in_memory", "LINES", "POLYLINE", spatial_reference=r_flowdir)
    lines = "in_memory\LINES"

    arcpy.AddField_management(lines, routeID_field, "LONG")
    linecursor = arcpy.da.InsertCursor(lines, ["SHAPE@", routeID_field])
    for tree in trees:
        for segment in tree.treesegments():
            totaldist = 0
            vertices = []
            if not segment.is_root():
                # les lignes commencent au dernier point du segment précédent
                vertices.append(arcpy.Point(segment.get_parent().get_profile()[-1].X, segment.get_parent().get_profile()[-1].Y))
            for pt in segment.get_profile():
                totaldist += pt.dist
                pointcursor.insertRow([(pt.X, pt.Y), pt.dist, totaldist, segment.id])
                vertices.append(arcpy.Point(pt.X, pt.Y))
            arc_vertices = arcpy.Array()
            vertices.reverse()
            for vertex in vertices:
                arc_vertices.add(vertex)
            line = arcpy.Polyline(arc_vertices)
            linecursor.insertRow([line, segment.id])

    # Create routes from start point to end point
    arcpy.AddField_management(lines, routeID_field, "LONG")
    arcpy.AddField_management(lines, "FromF", "FLOAT")
    arcpy.CalculateField_management(lines, "FromF", "0", "PYTHON")
    arcpy.AddGeometryAttributes_management(lines, "LENGTH_GEODESIC")
    arcpy.CreateRoutes_lr(lines, routeID_field, str_output_routes, "TWO_FIELDS", from_measure_field="FromF",
                          to_measure_field="LENGTH_GEO")
    arcpy.AddGeometryAttributes_management(str_output_routes, "LENGTH_GEODESIC")

    arcpy.AddXY_management(str_output_points)
    arcpy.AddField_management(str_output_points, "PointID", "LONG")
    arcpy.CalculateField_management(str_output_points, "PointID",  "!" + arcpy.Describe(str_output_points).OIDFieldName + "!", "PYTHON")


def execute_Q_width_ws_to_shapefile(pts, Q_dir, width_dir, ws_dir, output_folder, messages):


    arcpy.env.workspace = Q_dir
    rasterlist = arcpy.ListRasters()

    for raster in rasterlist:
        print (raster)
        outshape = os.path.join(output_folder, raster+".shp")
        width = os.path.join(width_dir, raster)
        ws = os.path.join(ws_dir, raster)
        arcpy.CopyFeatures_management(pts, outshape)
        inRasterList = [[raster, "Q"], [width, "width"],
                        [ws, "ws"]]
        arcpy.sa.ExtractMultiValuesToPoints(outshape, inRasterList)





class Messages():
    def addErrorMessage(self, text):
        print (text)

    def addMessage(self, text):
        print (text)

if __name__ == "__main__":
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True

    arcpy.env.scratchWorkspace = r"D:\InfoCrue\tmp"
    frompoints = r"D:\InfoCrue\Refontebathy\Inputs\dep_pts_simp.shp"
    flowdir = arcpy.Raster(r"D:\InfoCrue\Refontebathy\Inputs\d4fd")

    messages = Messages()

    from datetime import datetime

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    trees = load_trees_from_FlowDir(flowdir, frompoints)

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    ptsout = r"D:\InfoCrue\Refontebathy\ptsflowdir.shp"
    routesout = r"D:\InfoCrue\Refontebathy\routesflowdir.shp"

    i = 0
    for tree in trees:
        for segment, prev, cs in tree.browsepts():
            i += 1
    execute_TreeFromFlowDir(flowdir, frompoints, routesout, "RouteID", ptsout, messages)
    print i

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    # arcpy.env.scratchWorkspace = r"D:\InfoCrue\tmp"
    # frompoints = r"D:\InfoCrue\Nicolet\BathyFev2021\newbathy_assessment\dep_pts.shp"
    # flowdir = arcpy.Raster(r"D:\InfoCrue\Nicolet\BathyFev2021\newbathy_assessment\lidar10m_fd")
    ptsout = r"D:\InfoCrue\Nicolet\BathyFev2021\newbathy_assessment\ptsflowdir.shp"
    # routesout = r"D:\InfoCrue\Nicolet\BathyFev2021\newbathy_assessment\routesflowdir.shp"
    # messages = Messages()
    #
    # execute_TreeFromFlowDir(flowdir, frompoints, routesout, "RouteID", ptsout, messages)

    ptsfolder = r"D:\InfoCrue\Nicolet\BathyFev2021\newbathy_assessment\PathPoints_correct171130"
    Q_dir = r"D:\InfoCrue\Nicolet\BathyFev2021\newbathy_assessment\Q"
    width_dir = r"D:\InfoCrue\Nicolet\BathyFev2021\newbathy_assessment\largeur"
    ws_dir = r"D:\InfoCrue\Nicolet\BathyFev2021\newbathy_assessment\ResultWS_17_11_30"

    execute_Q_width_ws_to_shapefile(ptsout, Q_dir, width_dir, ws_dir, ptsfolder, messages)