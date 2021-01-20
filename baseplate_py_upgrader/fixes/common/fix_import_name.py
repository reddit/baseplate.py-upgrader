from lib2to3.fixer_util import find_indentation
from lib2to3.fixer_util import Name
from lib2to3.fixer_util import Node
from lib2to3.fixer_util import syms
from lib2to3.fixer_util import token

from . import NameRemovedError
from . import RenamedSymbols
from .. import BaseplateBaseFix
from .. import Capture
from .. import ImportAsName
from .. import LN
from .. import traverse_dotted_name


class BaseFixImportName(BaseplateBaseFix):
    PATTERN = """
    import_name< 'import'
        (
            module_names='baseplate'*
            |
            module_names=dotted_name< 'baseplate' any* >*
            |
            module_names=dotted_as_name< any* >*
            |
            dotted_as_names< module_names=any* >
        )
    >
    """

    @property
    def renames(self) -> RenamedSymbols:
        raise NotImplementedError

    def transform(self, node: LN, capture: Capture) -> None:
        imports = []
        for n in capture["module_names"]:
            if n.type == token.COMMA:
                pass
            elif n.type == token.NAME:
                imports.append((n.value, None))
            elif n.type == syms.dotted_name:
                imports.append((traverse_dotted_name(n), None))
            elif n.type == syms.dotted_as_name:
                import_name, import_nick = n.children[0], n.children[2]
                assert n.children[1].type == token.NAME and n.children[1].value == "as"
                imports.append((traverse_dotted_name(import_name), import_nick.value))

        rename_seen = False
        nodes = []
        indent = find_indentation(node)
        for name, nick in imports:
            try:
                new_name = self.renames.get_new_name(name)
            except NameRemovedError as exc:
                self.warn(node, str(exc))
                continue

            if new_name:
                rename_seen = True
                name = new_name
            new_node = Node(
                syms.import_name,
                [Name("import"), ImportAsName(name, nick, prefix=" ")],
                prefix=f"\n{indent}",
            )
            nodes.append(new_node)

        if not nodes:
            return

        nodes[0].prefix = node.prefix

        if rename_seen:
            node.replace(nodes)
