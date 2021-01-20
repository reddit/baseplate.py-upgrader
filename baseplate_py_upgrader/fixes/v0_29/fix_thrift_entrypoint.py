from lib2to3.fixer_util import Assign
from lib2to3.fixer_util import Call
from lib2to3.fixer_util import Comma
from lib2to3.fixer_util import Name
from lib2to3.fixer_util import Newline
from lib2to3.fixer_util import Node
from lib2to3.fixer_util import syms
from lib2to3.fixer_util import token
from typing import List
from typing import Optional
from typing import Tuple

from .. import BaseplateBaseFix
from .. import Capture
from .. import FromImport
from .. import LN
from .. import traverse_dotted_name


class FixThriftEntrypoint(BaseplateBaseFix):
    PATTERN = """
    (
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
        |
        power< NAME trailer< '.' iface_class='ContextIface' > any* >
        |
        simple_stmt<
        (
            make_processor=expr_stmt<
                NAME '='
                power< NAME trailer <'.' processor_class='ContextProcessor'> any*>
            >
            |
            make_event_handler=expr_stmt<
                NAME '=' power<
                    'BaseplateProcessorEventHandler'
                    trailer<
                        '('
                        arglist<
                            arguments=any*
                        >
                        ')'
                    >
                >
            >
            |
            set_event_handler=power< processor_name=NAME trailer<'.' 'setEventHandler'> any* >
        ) any*>
    )
    """

    def transform(self, node: LN, capture: Capture) -> None:
        if node.type == syms.import_from:
            module_name = traverse_dotted_name(capture["module_name"])
            if module_name != "baseplate.integration.thrift":
                return

            to_process = capture["module_imports"]
            imports: List[Tuple[str, Optional[str]]] = []
            for n in to_process:
                if n.type in (token.COMMA, token.LPAR, token.RPAR):
                    continue
                elif n.type == token.STAR:
                    imports.append(("*", None))
                elif n.type == token.NAME:
                    if n.value == "BaseplateProcessorEventHandler":
                        imports.append(("baseplateify_processor", None))
                    else:
                        imports.append((n.value, None))
                elif n.type == syms.import_as_name:
                    import_name, import_nick = n.children[0], n.children[2]
                    assert (
                        n.children[1].type == token.NAME and n.children[1].value == "as"
                    )

                    if import_name.value == "BaseplateProcessorEventHandler":
                        self.warn(
                            n,
                            "BaseplateProcessorEventHandler aliased, make sure uses are removed.",
                        )
                        continue

                    imports.append(
                        (import_name.value, import_nick.value if import_nick else None)
                    )
                elif n.type == syms.import_as_names:
                    to_process.extend(n.children)
                else:
                    raise Exception(f"unexpected node {repr(n)}")

            if imports:
                node.replace(FromImport(module_name, imports, prefix=node.prefix))
            else:
                node.remove()
        elif node.type == syms.power:
            capture["iface_class"].replace(Name("Iface"))
        elif node.type == syms.simple_stmt:
            if "make_processor" in capture:
                capture["processor_class"].replace(Name("Processor"))
            elif "make_event_handler" in capture:
                self.arguments = [arg.clone() for arg in capture["arguments"]]
                self.remove_me = node
            elif "set_event_handler" in capture:
                processor_name = capture["processor_name"].clone()
                processor_name.prefix = ""
                arguments = [processor_name, Comma()]
                original_arguments = getattr(self, "arguments", None)
                if original_arguments:
                    original_arguments[0].prefix = " "
                    arguments.extend(original_arguments)
                else:
                    arguments.extend(
                        (
                            Name("logger", prefix=" "),
                            Comma(),
                            Name("baseplate", prefix=" "),
                        )
                    )

                node.replace(
                    [
                        Assign(
                            capture["processor_name"].clone(),
                            Node(
                                syms.simple_stmt,
                                [Call(Name("baseplateify_processor"), arguments)],
                            ),
                        ),
                        Newline(),
                    ]
                )

                if hasattr(self, "remove_me"):
                    self.remove_me.remove()
        else:
            raise Exception("unrecognized match")
