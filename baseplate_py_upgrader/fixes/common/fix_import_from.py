import collections

from lib2to3.fixer_util import find_indentation
from lib2to3.fixer_util import Name
from lib2to3.fixer_util import Node
from lib2to3.fixer_util import syms
from lib2to3.fixer_util import token
from typing import DefaultDict
from typing import List
from typing import Optional
from typing import Tuple

from . import NameRemovedError
from . import RenamedSymbols
from .. import BaseplateBaseFix
from .. import Capture
from .. import FromImport
from .. import ImportAsName
from .. import LN
from .. import split_package_and_name
from .. import traverse_dotted_name


class BaseFixImportFrom(BaseplateBaseFix):
    PATTERN = """
    import_from<
        'from'
        (
            module_name='baseplate'
            |
            module_name=dotted_name< 'baseplate' any* >
        )
        'import' ['(']
        (
            import_as_names< module_imports=any* >
            |
            module_imports=any*
        )
        [')']
    >
    """

    @property
    def renames(self) -> RenamedSymbols:
        raise NotImplementedError

    def transform(self, node: LN, capture: Capture) -> None:
        module_name = traverse_dotted_name(capture["module_name"])

        to_process = capture["module_imports"]
        imports: List[Tuple[str, Optional[str]]] = []
        for n in to_process:
            if n.type in (token.COMMA, token.LPAR, token.RPAR):
                continue
            elif n.type == token.STAR:
                self.warn(n, "Cannot guarantee * imports are correct.")
                imports.append(("*", None))
            elif n.type == token.NAME:
                imports.append((n.value, None))
            elif n.type == syms.import_as_name:
                import_name, import_nick = n.children[0], n.children[2]
                assert n.children[1].type == token.NAME and n.children[1].value == "as"
                imports.append(
                    (import_name.value, import_nick.value if import_nick else None)
                )
            elif n.type == syms.import_as_names:
                to_process.extend(n.children)
            else:
                raise Exception(f"unexpected node {repr(n)}")

        imports_by_package: DefaultDict[
            str, List[Tuple[str, Optional[str]]]
        ] = collections.defaultdict(list)
        for name, nick in imports:
            full_name = f"{module_name}.{name}"
            try:
                new_full_name = self.renames.get_new_name(full_name) or full_name
            except NameRemovedError as exc:
                self.warn(node, str(exc))
                continue
            package, new_name = split_package_and_name(new_full_name)
            if name != new_name and nick is None:
                nick = name
            imports_by_package[package].append((new_name, nick))

        indent = find_indentation(node)
        nodes = []
        for package, imports in sorted(imports_by_package.items(), key=lambda i: i[0]):
            if package:
                result = FromImport(package, imports, prefix=f"\n{indent}")
                nodes.append(result)
            else:
                for name, nick in imports:
                    nodes.append(
                        Node(
                            syms.import_name,
                            [Name("import"), ImportAsName(name, nick, prefix=" ")],
                            prefix=f"\n{indent}",
                        )
                    )

        if not nodes:
            return

        nodes[0].prefix = node.prefix
        node.replace(nodes)
