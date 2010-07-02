from collections import namedtuple
from enums import Enum

VERSION = "0.1"

Header = Enum(['NONE', 'FIRSTROW', 'AUTODETECT'])
ColumnType = Enum(['INT', 'REAL', 'STRING', 'DATE', 'TIME', 'DATETIME', 'BOOL'])
ColumnGeometry = Enum(['NONE', 'GEOM', 'X', 'Y'])
Column = namedtuple('Column', 'name type geometry')

class InvalidFilenameError(ValueError):
    pass

class InvalidGeometryError(ValueError):
    pass


def set_field_geometry(fields, geom_val, geom_is_xy, geom_is_numeric):
    if geom_is_numeric:
        if geom_is_xy:
            fields[geom_val[0]] = Column(fields[geom_val[0]].name, fields[geom_val[0]].type, ColumnGeometry.X)
            fields[geom_val[1]] = Column(fields[geom_val[1]].name, fields[geom_val[1]].type, ColumnGeometry.Y)
        else:
            fields[geom_val] = Column(fields[geom_val].name, fields[geom_val].type, ColumnGeometry.GEOM)
    else:
        if geom_is_xy:
            found = set()
            for i, f in enumerate(list(fields)):
                if len(found) >= 2:
                    break
                if f.name == geom_val[0]:
                    fields[i] = Column(f.name, f.type, ColumnGeometry.X)
                    found.add('x')
                elif f.name == geom_val[1]:
                    fields[i] = Column(f.name, f.type, ColumnGeometry.Y)
                    found.add('y')
            if len(found) != 2:
                raise KeyError, "Could not find geometry columns '%s' and '%s'" % (geom_val[0], geom_val[1])
        else:
            found = False
            for i, f in enumerate(list(fields)):
                if f.name == geom_val:
                    fields[i] = Column(f.name, f.type, ColumnGeometry.GEOM)
                    found = True
                    break
            if not found:
                raise KeyError, "Could not find geometry column '%s'" % geom_val
    return fields
