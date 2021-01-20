import itertools

from lib2to3.fixer_util import Call
from lib2to3.fixer_util import Comma
from lib2to3.fixer_util import KeywordArg
from lib2to3.fixer_util import Name
from lib2to3.fixer_util import syms
from lib2to3.fixer_util import token
from lib2to3.fixer_util import touch_import
from typing import Any
from typing import Iterable
from typing import Tuple
from typing import TypeVar

from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


T = TypeVar("T")


def pairwise(iterable: Iterable[T]) -> Iterable[Tuple[T, T]]:
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class FixTrustTraceHeaders(BaseplateBaseFix):
    PATTERN = """
        simple_stmt<
            expr_stmt<
                NAME '=' power<
                  'BaseplateConfigurator'
                  trailer<
                      '('
                      arglist=arglist<
                          arguments=any*
                      >
                      ')'
                  >
                >
            >
            any*
        >
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.added_static_trust_handler = False

    def transform(self, node: LN, capture: Capture) -> None:
        if node.type == syms.simple_stmt:
            trust_trace_headers_value = None
            header_trust_handler_seen = False

            for prev_argument, argument in pairwise(capture["arguments"]):
                if argument.type == syms.argument:
                    if argument.children[0].value == "trust_trace_headers":
                        assert argument.children[1].value == "="
                        trust_trace_headers_value = argument.children[2].clone()
                        argument.remove()

                        if prev_argument.type == token.COMMA:
                            prev_argument.remove()
                    elif argument.children[0].value == "header_trust_handler":
                        header_trust_handler_seen = True

            if trust_trace_headers_value and not header_trust_handler_seen:
                capture["arglist"].append_child(Comma())

                handler_kwarg = KeywordArg(
                    Name("trust_headers"), trust_trace_headers_value
                )
                handler = Call(Name("StaticTrustHandler"), args=[handler_kwarg])

                kwarg = KeywordArg(Name("header_trust_handler"), handler)
                kwarg.prefix = " "
                capture["arglist"].append_child(kwarg)

                self.added_static_trust_handler = True

    def finish_tree(self, tree: LN, filename: str) -> None:
        if self.added_static_trust_handler:
            touch_import("baseplate.frameworks.pyramid", "StaticTrustHandler", tree)
