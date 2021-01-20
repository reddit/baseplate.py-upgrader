from . import RENAMES
from ..common.fix_import_name import BaseFixImportName


class FixImportName(BaseFixImportName):
    renames = RENAMES
