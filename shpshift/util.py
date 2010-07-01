from collections import namedtuple
from enums import Enum

VERSION = "0.1"

Header = Enum(['NONE', 'FIRSTROW', 'AUTODETECT'])
Column = namedtuple('Column', 'name type')
ColumnType = Enum(['INT', 'REAL', 'STRING', 'DATE', 'TIME', 'DATETIME'])
