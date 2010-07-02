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

class ShpWriter(object): 
    def __init__(self, filename, fields, srs=None, overwrite=False):
        self._filename = filename
        self._fields = fields
        self._srs = srs
        self._overwrite = overwrite
        if overwrite:
            self._delete_any_shapefiles()
        shps = list(self._find_shapefiles())
        if len(shps) > 0:
            raise IOError, "Files %s and '%s' already exist.  Use '--force' to overwrite." % (
                ', '.join(["'%s'" % s for s in shps[:-1]]), shps[-1])
            

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

    def _delete_any_shapefiles(self):
        for f in self._find_shapefiles():
            os.unlink(f)
