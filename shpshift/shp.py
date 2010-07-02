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
    def __init__(self, filename, fields, srs=None, overwrite=False):
        self._filename = filename
        self._fields = fields
        self._srs = srs
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

    def _find_shapefiles(self):
        shp_exts = ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.qix']
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
