from lib2to3.fixer_util import Node
from lib2to3.fixer_util import syms
from lib2to3.fixer_util import token
from typing import List

from . import NameRemovedError
from . import RenamedSymbols
from .. import AttrChain
from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


class BaseFixModuleUsage(BaseplateBaseFix):
    PATTERN = """
    module_name=power<
        [TOKEN]
        'baseplate'
        module_access=trailer< any* >*
    >
    """

    @property
    def renames(self) -> RenamedSymbols:
        raise NotImplementedError

    def transform(self, node: LN, capture: Capture) -> None:
        full_name = []
        trailer: List[LN] = []
        for i, n in enumerate(node.children):
            if n.type == token.NAME:
                full_name.append(n.value)
            elif n.type == syms.trailer:
                if n.children[0].type != token.DOT:
                    trailer = node.children[i:]
                    break
                full_name.append(n.children[1].value)
            else:
                trailer = node.children[i:]

        try:
            new_name = self.renames.get_new_name(".".join(full_name))
        except NameRemovedError as exc:
            self.warn(node, str(exc))
            return

        if new_name:
            new_node = Node(syms.power, AttrChain(new_name), prefix=node.prefix)
            for n in trailer:
                new_node.append_child(n)
            node.replace(new_node)
