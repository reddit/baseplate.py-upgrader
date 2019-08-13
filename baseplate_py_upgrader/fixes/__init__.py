import logging

from lib2to3.fixer_base import BaseFix
from lib2to3.fixer_util import Comma
from lib2to3.fixer_util import Dot
from lib2to3.fixer_util import Leaf
from lib2to3.fixer_util import Name
from lib2to3.fixer_util import Node
from lib2to3.fixer_util import syms
from lib2to3.fixer_util import token
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union


LN = Union[Node, Leaf]
Capture = Dict[str, LN]


logger = logging.getLogger(__name__)


class BaseplateBaseFix(BaseFix):
    def warn(self, node: LN, message: str) -> None:
        logger.warning("Line %d of %s: %s", node.get_lineno(), self.filename, message)


def split_package_and_name(dotted_name: str) -> Tuple[str, str]:
    *module, name = dotted_name.split(".")
    return (".".join(module), name)


def traverse_dotted_name(dotted_name: LN) -> str:
    result = []
    for part in dotted_name.leaves():
        assert part.type in (
            token.NAME,
            token.DOT,
            token.STAR,
        ), f"unexpected {repr(part)}"
        result.append(part.value)
    return "".join(result)


def DottedName(full_name: str, prefix: Optional[str]) -> Node:
    names = [name.strip() for name in full_name.split(".")]

    dotted_name = []
    for name in names:
        dotted_name.append(Name(name))
        dotted_name.append(Dot())
    dotted_name.pop()

    return Node(syms.dotted_name, dotted_name, prefix=prefix)


def ImportAsName(name: str, nick: Optional[str], prefix: Optional[str] = None) -> Node:
    if not nick:
        return Name(name, prefix=prefix)
    return Node(
        syms.import_as_name,
        [Name(name), Name("as", prefix=" "), Name(nick, prefix=" ")],
        prefix=prefix,
    )


def FromImport(
    package: str, imports: List[Tuple[str, Optional[str]]], prefix: Optional[str]
) -> Node:
    children = []
    for name, nick in imports:
        children.append(ImportAsName(name, nick, prefix=" "))
        children.append(Comma())
    children.pop()
    import_as_names = Node(syms.import_as_names, children)

    return Node(
        syms.import_from,
        [
            Name("from", prefix=prefix),
            DottedName(package, prefix=" "),
            Name("import", prefix=" "),
            import_as_names,
        ],
    )


def AttrChain(name: str) -> List[Node]:
    first, *rest = name.split(".")
    children = [Name(first)]
    for attr in rest:
        children.append(Node(syms.trailer, [Dot(), Name(attr)]))
    return children
