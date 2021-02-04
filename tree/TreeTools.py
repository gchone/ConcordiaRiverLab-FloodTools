# -*- coding: utf-8 -*-

### Historique des versions ###
# v1.0 - Jan 2021 - Création - Guénolé Choné

# ArcGIS tools for tree manipulation


from tree.OurTreeManager import *
from RasterIO import *


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
        newtreeseg = OurTreeSegment(segmentid)
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
                    newchild = OurTreeSegment(segmentid)
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
                tree = OurTreeManager()
                tree.treeroot = newtreeseg
                trees.append(tree)

    for tree in trees:
        print (tree)

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
                vertices.append(arcpy.Point(segment.get_parent().__ptsprofile[-1].X, segment.get_parent().__ptsprofile[-1].Y))
            for pt in segment.__ptsprofile:
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
    frompoints = r"D:\InfoCrue\Etchemin\DEMbydays\dep_pts.shp"
    flowdir = arcpy.Raster(r"D:\InfoCrue\Etchemin\DEMbydays\d4fd")
    ptsout = r"D:\InfoCrue\tmp\testbed\ptsflowdir.shp"
    routesout = r"D:\InfoCrue\tmp\testbed\routesflowdir.shp"
    messages = Messages()

    execute_TreeFromFlowDir(flowdir, frompoints, routesout, "RouteID", ptsout, messages)

    ptsfolder = r"D:\InfoCrue\tmp\testbed\PathPoints"
    Q_dir = r"D:\InfoCrue\Etchemin\DEMbydays\Qlidar\QLiDAR_dir_buf"
    width_dir = r"D:\InfoCrue\Etchemin\DEMbydays\Widthcalc\WidthD4"
    ws_dir = r"D:\InfoCrue\Etchemin\DEMbydays\wscorrectionprise4\ResultWSD4"

    execute_Q_width_ws_to_shapefile(ptsout, Q_dir, width_dir, ws_dir, ptsfolder, messages)