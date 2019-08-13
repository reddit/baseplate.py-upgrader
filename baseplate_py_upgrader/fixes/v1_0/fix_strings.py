# this comment is here to prevent reorder-python-imports from getting confused
# because there are _only_ relative imports. remove as soon as some other
# import comes first.

from . import replace_module_references
from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


class FixStrings(BaseplateBaseFix):
    PATTERN = "STRING"

    def transform(self, node: LN, capture: Capture) -> None:
        new_text = replace_module_references(node.value)
        if new_text != node.value:
            node.value = new_text
            node.changed()
