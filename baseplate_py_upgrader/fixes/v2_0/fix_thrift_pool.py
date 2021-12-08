from lib2to3.fixer_util import Name
from lib2to3.fixer_util import syms
from typing import Any

from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


class FixThriftPool(BaseplateBaseFix):
    PATTERN = """
        power<
          ( 'thrift_pool_from_config' | 'ThriftConnectionPool' | 'ThriftClient' )
          trailer<
              '('
              arglist=arglist<
                  arguments=any*
              >
              ')'
          >
        >
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.added_static_trust_handler = False

    def transform(self, node: LN, capture: Capture) -> None:
        for argument in capture["arguments"]:
            if argument.type == syms.argument and argument.children[1].value == "=":
                keyword_name = argument.children[0]

                if keyword_name.value == "max_retries":
                    keyword_name.replace(
                        Name("max_connection_attempts", prefix=keyword_name.prefix)
                    )
