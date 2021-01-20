from lib2to3.fixer_util import Name

from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


RENAMES = {"trace": "span", "request_context": "edge_context"}


class FixContextAttributes(BaseplateBaseFix):
    PATTERN = f"""
      (
       power<
        ('request' | 'context')
        trailer< '.' ({" | ".join("attribute_name='%s'" % name for name in RENAMES)})>
        any*
       >
       |
       power<
        NAME
        trailer< '.' NAME>*
        trailer< '.' ('request' | 'context')>
        trailer< '.' ({" | ".join("attribute_name='%s'" % name for name in RENAMES)})>
        any*
       >
      )
    """

    def transform(self, node: LN, capture: Capture) -> None:
        attribute_node = capture["attribute_name"]
        new_name = RENAMES[attribute_node.value]
        attribute_node.replace(Name(new_name))
