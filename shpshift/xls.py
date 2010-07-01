import xlrd
from util import Header
from util import Column
from util import ColumnType

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

    def fields(self):
        # get the fieldnames, and find the index of the first value row
        if self._header == Header.FIRSTROW:
            typerow_idx = 1
            col_names = [str(x.value) for x in self._sheet.row(0)]
        else:
            typerow_idx = 0
            col_names = ["Field%03d" % x for x in range(len(typerow))]

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
                    types[colnum] = ColumnType.INT
                elif cell.ctype == xlrd.XL_CELL_ERROR:
                    continue
                untyped_cols.remove(colnum)
            typerow_idx += 1
        # Any column we can't detect the type of defaults to string
        for colnum in untyped_cols:
            types[colnum] = ColumnType.STRING
        return zip(col_names, types)

    def detect_header_type(self):
        """
        Detects whether or not a workbook has a header row.

        A header row is detected if and only if:
         * All cells in the first row are of type 'text', and
         * At least one cell in the second row is not of type 'text'

        """

        for cell in self._sheet.row(0):
            if cell.ctype != xlrd.XL_CELL_TEXT:
                return Header.NONE

        for cell in self._sheet.row(1):
            if cell.ctype != xlrd.XL_CELL_TEXT:
                return Header.FIRSTROW

        # All cells in the second row are text
        return Header.NONE


    def read(self):
        pass
