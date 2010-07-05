import datetime
import xlrd
from util import *

class XlsReader(object): 
    def __init__(self, filename=None, sheet_number=0, header=Header.AUTODETECT, file_contents=None):
        # Can only have one of filename or file contents
        if filename is None and file_contents is None:
            raise ValueError, "either a filename or file_contents required"
        elif not filename is None and not file_contents is None:
            raise ValueError, "cannot process both a filename and a file_contents"
        self._filename = filename
        self._file_contents = file_contents
        self._sheet_number = sheet_number
        self._header = header
        self.__fields = None # for caching the call to fields() in
        # open book for reading
        if self._filename is None:
            try:
                self._book = xlrd.open_workbook(file_contents=file_contents, formatting_info=True)
            except (TypeError, xlrd.biffh.XLRDError), e:
                raise ValueError, "spreadsheet contents invalid or corrupt"
        else:
            self._book = xlrd.open_workbook(self._filename, formatting_info=True)
        try:
            self._sheet = self._book.sheet_by_index(self._sheet_number) 
        except IndexError, e:
            raise ValueError, "sheet %d was not found in spreadsheet" % self._sheet_number
        # ensure a consistent header type
        if header == Header.AUTODETECT:
            self._header = self.detect_header_type()
        
    def _format_str(self, cell):
        return self._book.format_map[self._book.xf_list[cell.xf_index].format_key].format_str

    def _numeric_type(self, format_str):
        if format_str.lower() == 'general':
            # We might want to auto-detect this in future
            return ColumnType.REAL
        elif ('.' in format_str) or ('E+' in format_str):
            return ColumnType.REAL
        else:
            return ColumnType.INT
        
    @property
    def _body_start_row(self):
        return (1 if self._header == Header.FIRSTROW else 0)
    
    def _translate(self, cell, column):
        if cell.ctype in [xlrd.XL_CELL_EMPTY,
                          xlrd.XL_CELL_BLANK,
                          xlrd.XL_CELL_ERROR]:
            return None
        translate = {ColumnType.STRING: unicode,
                     ColumnType.INT: int,
                     ColumnType.REAL: float,
                     ColumnType.DATETIME: (lambda x: datetime.datetime(*xlrd.xldate_as_tuple(float(x), self._book.datemode))),
                     ColumnType.BOOL: bool}
        return translate[column.type](cell.value)

    def row(self, idx):
        return [self._translate(cell, self.fields[i]) for i, cell in enumerate(self._sheet.row(idx + self._body_start_row))]

    def read(self):
        f = self.fields
        t = self._translate
        for i in xrange(self._body_start_row, self._sheet.nrows):
            yield [t(cell, f[i]) for i, cell in enumerate(self._sheet.row(i))]

    @property
    def fields(self):
        if not self. __fields is None:
            return self.__fields

        typerow_idx = self._body_start_row
        # get the fieldnames, and find the index of the first value row
        if self._header == Header.FIRSTROW:
            col_names = [str(x.value) for x in self._sheet.row(0)]
        else:
            col_names = ["Field%03d" % x for x in range(len(self._sheet.row(typerow_idx)))]

        # detect the datatypes of the cells.  If the cell is blank, skip it and try the next row
        ncols = len(col_names)
        types = [None] * ncols
        untyped_cols = set(range(ncols))
        while len(untyped_cols) > 0 and typerow_idx < self._sheet.nrows:
            row = self._sheet.row(typerow_idx)
            # Make a copy of untyped_cols so we can remove items while iterating
            for colnum in list(untyped_cols):
                cell = row[colnum]
                if (cell.ctype == xlrd.XL_CELL_EMPTY) or (
                    cell.ctype == xlrd.XL_CELL_BLANK):
                    continue
                elif cell.ctype == xlrd.XL_CELL_TEXT:
                    types[colnum] = ColumnType.STRING
                elif cell.ctype == xlrd.XL_CELL_NUMBER:
                    types[colnum] = self._numeric_type(self._format_str(cell))
                elif cell.ctype == xlrd.XL_CELL_DATE:
                    types[colnum] = ColumnType.DATETIME
                elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                    types[colnum] = ColumnType.BOOL
                elif cell.ctype == xlrd.XL_CELL_ERROR:
                    continue
                untyped_cols.remove(colnum)
            typerow_idx += 1
        # Any column we can't detect the type of defaults to string
        for colnum in untyped_cols:
            types[colnum] = ColumnType.STRING
#         self.__fields = zip(col_names, types)
        self.__fields = [Column(col_names[i], types[i], ColumnGeometry.NONE) for i in xrange(0, ncols)]
        return self.__fields

    def detect_header_type(self):
        """
        Detects whether or not a workbook has a header row.

        A header row is detected if and only if:
         * All cells in the first row are of type 'text', and
         * At least one cell in the second row is not of type 'text'

        """
        self.__fields = None

        for cell in self._sheet.row(0):
            if not cell.ctype in [xlrd.XL_CELL_TEXT, xlrd.XL_CELL_EMPTY]:
                return Header.NONE

        for cell in self._sheet.row(1):
            if not cell.ctype in [xlrd.XL_CELL_TEXT, xlrd.XL_CELL_EMPTY]:
                return Header.FIRSTROW

        # All cells in the second row are text
        return Header.NONE

    def set_field_geom(self, geom_val, geom_is_xy, geom_is_numeric, prj_col_defined, prj_col_val, prj_col_is_numeric):
        fields = self.fields
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
                    if f.name.lower() == geom_val[0].lower():
                        fields[i] = Column(f.name, f.type, ColumnGeometry.X)
                        found.add('x')
                    elif f.name.lower() == geom_val[1].lower():
                        fields[i] = Column(f.name, f.type, ColumnGeometry.Y)
                        found.add('y')
                if len(found) != 2:
                    raise KeyError, "Could not find geometry columns '%s' and '%s'" % (geom_val[0], geom_val[1])
            else:
                found = False
                for i, f in enumerate(list(fields)):
                    if f.name.lower() == geom_val.lower():
                        fields[i] = Column(f.name, f.type, ColumnGeometry.GEOM)
                        found = True
                        break
                if not found:
                    raise KeyError, "Could not find geometry column '%s'" % geom_val
            if prj_col_defined:
                if prj_col_is_numeric:
                    fields[prj_col_val] = Column(fields[prj_col_val].name, fields[prj_col_val].type, ColumnGeometry.SRS)
                else:
                    found = False
                    for i, f in enumerate(list(fields)):
                        if f.name.lower() == prj_col_val.lower():
                            fields[i] = Column(f.name, f.type, ColumnGeometry.SRS)
                            found = True
                            break
                    if not found:
                        raise KeyError, "Could not find spatial reference system column '%s'" % prj_col_val
        self._fields = fields
        return fields
