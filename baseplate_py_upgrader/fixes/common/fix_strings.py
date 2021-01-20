from . import RenamedSymbols
from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


class BaseFixStrings(BaseplateBaseFix):
    PATTERN = "STRING"

    @property
    def renames(self) -> RenamedSymbols:
        raise NotImplementedError

    def transform(self, node: LN, capture: Capture) -> None:
        new_text = self.renames.replace_module_references(node.value)
        if new_text != node.value:
            node.value = new_text
            node.changed()
