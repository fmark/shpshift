import os
import glob

try:
    from osgeo import ogr
except ImportError:
    import ogr
try:
    from osgeo import osr
except ImportError:
    import osr

from util import Column
from util import ColumnType
from util import ColumnGeometry
from util import InvalidFilenameError

ogr.UseExceptions()

class ShpWriter(object): 
    def __init__(self, filename, reader, srs=None, overwrite=False):
        self._filename = filename
        self._reader = reader
        if srs is None: 
            self._srs = None
        else:
            self._srs = osr.SpatialReference()
            self._srs.SetFromUserInput(srs)

        self._srs_transforms = {}
        self._drv = ogr.GetDriverByName('ESRI Shapefile')
        self._overwrite = overwrite
        self._validate_filename()
        if overwrite:
            self._delete_any_shapefiles()
        shps = list(self._find_shapefiles())
        if len(shps) > 0:
            raise IOError, "Files %s and '%s' already exist.  Use '--force' to overwrite." % (
                ', '.join(["'%s'" % s for s in shps[:-1]]), shps[-1])
        self._create_shp()
        
        
    def _create_shp(self):
        drv = ogr.GetDriverByName( 'ESRI Shapefile' )
        try:
            self._ds = drv.CreateDataSource(self._filename)
            self._lyr = self._ds.CreateLayer( "points", self._srs, ogr.wkbPoint )
        except Exception, e:
            raise IOError, "Could not create shapefile '%s': %s" % (self._filename, e)
        self._detect_geom()
        self._create_shp()
        self._add_fields()
        self._write_utf8()

    def _write_utf8(self):
        self._ds.SyncToDisk()
        # ensure that the LDID of the shapefile is zero
        f = open(self._filename, 'r+b')
        f.seek(0x1D)
        f.write('\x00')
        f.close()
        # now write out a .cpg file containing the string UTF-8
        bname, ext = os.path.splitext(self._filename)
        f = open(bname + '.cpg', 'w')
        f.write('UTF-8')
        f.close()

    def _write_row(self, row, lyr_dfn):
        # write attributes
        try:
            feat = ogr.Feature(lyr_dfn)
            # Set field values
            for i, f in enumerate(self._reader.fields):
                # Need to check if utf-8 is widely supported
                if not row[i] is None and f.type == ColumnType.STRING:
                    row[i] = row[i].encode('utf-8')
                feat.SetField(i, row[i])
            # Create geometry
            if len(self._geom_cols) == 1:
                if row[self._geom_cols[0]] is None:
                    return
                geom = ogr.CreateGeometryFromWkt(row[self._geom_cols[0]])
            else:
                for field_idx in self._geom_cols:
                    if self._reader.fields[field_idx].geometry == ColumnGeometry.X:
                        x = row[field_idx]
                    elif self._reader.fields[field_idx].geometry == ColumnGeometry.Y:
                        y = row[field_idx]
                if x is None or y is None:
                    return
                geom = ogr.Geometry(ogr.wkbPoint)
                geom.SetPoint_2D(0, x, y)
            # Transform the SRS if necessary
            if not (self._prj_col is None or row[self._prj_col] is None):
                self._transform_geom(geom, row[self._prj_col])
            # Save geometry
            feat.SetGeometry(geom)
            self._lyr.CreateFeature(feat)
        finally:
            feat.Destroy()

    def write_row(self, row_idx):
        lyr_dfn = self._lyr.GetLayerDefn()
        row = self._reader.row(row_idx)
        self._write_row(row, lyr_dfn)
                
    def write(self):
        lyr_dfn = self._lyr.GetLayerDefn()
        for row in self._reader.read():
            self._write_row(row, lyr_dfn)

    def _transform_geom(self, geom, srs_str):
        if not srs_str in self._srs_transforms:
            to_srs = osr.SpatialReference()
            to_srs.SetFromUserInput(srs_str)
            self._srs_transforms[srs_str] = osr.CoordinateTransformation(
                self._srs, to_srs)
        geom.Transform(self._srs_transforms[srs_str])
>>>>>>> origin/master

    def _find_shapefiles(self):
        shp_exts = ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', 
                    '.qix', '.fbn', '.fbx', '.ain', '.aih', '.ixs',
                    '.mxs', '.atx', '.shp.xml', '.cpg']
        # .qix is the OGR index, all other extensions are listed
        # on wikipedia
        absname = os.path.realpath(self._filename)
        dir = os.path.dirname(absname)
        nameroot, nameext = os.path.splitext(os.path.basename(absname))

        files = []
        for f in glob.glob("%s%s%s%s" % (dir, os.path.sep, nameroot, '.*')):
            _, ext = os.path.splitext(f)
            if ext in shp_exts:
                yield f
    
    def _validate_filename(self):
        _, ext = os.path.splitext(self._filename)
        if ext != '.shp':
            raise InvalidFilenameError, "'%s' is not a valid shapefile filename" % self._filename

    def _delete_any_shapefiles(self):
        for f in self._find_shapefiles():
            os.unlink(f)

    def _create_shp(self):
        self._ds = self._drv.CreateDataSource(self._filename)
        self._lyr = self._ds.CreateLayer( "points", self._srs, self._geom_type)

    def _add_fields(self):
        def fields_to_ogr(fields):
            lookup = {ColumnType.REAL: ogr.OFTReal,
                      ColumnType.INT: ogr.OFTInteger,
                      ColumnType.STRING: ogr.OFTString,
                      ColumnType.DATE: ogr.OFTDate,
                      ColumnType.TIME: ogr.OFTTime,
                      ColumnType.DATETIME: ogr.OFTDateTime,
                      ColumnType.BOOL: ogr.OFTInteger}
            return [(f.name, lookup[f.type]) for f in fields]

        for name, type in fields_to_ogr(self._reader.fields):
            try:
                field_defn = ogr.FieldDefn(name, type)
                self._lyr.CreateField(field_defn)
            finally:
                field_defn.Destroy()

    def _detect_geom(self):
        self._prj_col = None
        self._geom_cols = []
        found = set()
        for i, f in enumerate(self._reader.fields):
            if f.geometry == ColumnGeometry.GEOM:
                self._geom_cols = [i]
                self._geom_type = self._detect_geom_type(i)
            elif f.geometry == ColumnGeometry.X and not 'x' in found:
                self._geom_cols.append(i)
                self._geom_type = ogr.wkbPoint
                found.add('x')
            elif f.geometry == ColumnGeometry.Y and not 'y' in found:
                self._geom_cols.append(i)
                self._geom_type = ogr.wkbPoint
                found.add('y')
            elif f.geometry == ColumnGeometry.SRS:
                if self._srs is None:
                    InvalidGeometryError, "Cannot transform coordinate systems if no output coordinate system is set"
                self._prj_col = i
        if len(self._geom_cols) == 0:
            raise InvalidGeometryError, "No geometry column set"
                
    def _detect_geom_type(self, colnum):
        row = self._reader.row(0)
        cell = row[colnum]
        #delete whitespace
        cellstr = ''.join(str(cell).split())
        geom_type = cellstr.split('(')[0].lower()
        lookup_geom = {'geometry': ogr.wkbUnknown,
                       'point': ogr.wkbPoint,
                       'linestring': ogr.wkbLineString,
                       'polygon': ogr.wkbPolygon,
                       'multipoint': ogr.wkbMultiPoint,
                       'multilinestring': ogr.wkbMultiLineString,
                       'multipolygon': ogr.wkbMultiPolygon,
                       'geometrycollection': ogr.wkbGeometryCollection,
                       'pointz': ogr.wkbPoint25D,
                       'linestring': ogr.wkbLineString25D,
                       'polygonz': ogr.wkbPolygon25D,
                       'multipointz': ogr.wkbMultiPoint25D,
                       'multilinestringz': ogr.wkbMultiLineString25D,
                       'multipolygonz': ogr.wkbMultiPolygon25D,
                       'geometrycollectionz': ogr.wkbGeometryCollection25D}
        try:
            return lookup_geom[geom_type]
        except KeyError:
            raise InvalidGeometryError, "Could not determine geometry type for '%s'" % cell
                       
                           
