from lib2to3.fixer_util import syms

from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


class FixDeprecatedWireup(BaseplateBaseFix):
    PATTERN = """
        (
           power< name='Baseplate' trailer< '(' args=any* ')' > > |
           power<
            NAME
            trailer< '.' (name='configure_observers' | name='configure_context') >
            trailer< '(' args=any* ')' >
            any*
          >
        )
    """

    def transform(self, node: LN, capture: Capture) -> None:
        args = capture["args"]
        if len(args) == 1 and args[0].type == syms.arglist:
            args = args[0].children

        if capture["name"].value == "Baseplate":
            # baseplate = Baseplate(app_config)
            if len(args) == 1:
                return

        if capture["name"].value == "configure_observers":
            # baseplate.configure_observers()
            if len(args) == 0:
                return

            # baseplate.configure_observers(module_name='foo')
            if len(args) == 1 and args[0].type == syms.argument:
                return

        if capture["name"].value == "configure_context":
            # baseplate.configure_context({})
            if len(args) == 1:
                return

        self.warn(
            node,
            "Pass config to the Baseplate constructor. " "See: https://github.com/reddit/baseplate.py-upgrader/wiki/v1.3#pass-your-applications-config-to-the-baseplate-constructor",
        )
