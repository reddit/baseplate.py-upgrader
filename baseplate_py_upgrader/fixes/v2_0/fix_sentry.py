from lib2to3.fixer_util import ArgList
from lib2to3.fixer_util import Comma
from lib2to3.fixer_util import Name
from lib2to3.fixer_util import String
from lib2to3.fixer_util import syms
from lib2to3.fixer_util import token

from .. import BaseplateBaseFix
from .. import Capture
from .. import LN


METHOD_RENAMES = {
    "captureException": "capture_exception",
    "captureMessage": "capture_message",
}
ARG_RENAMES = {
    "exc_info": "error",
    "extra": "extras",
    "tags": "tags",
    "message": "message",
}


class FixSentry(BaseplateBaseFix):
    PATTERN = f"""
      (
       power<
        NAME
        trailer< '.' 'sentry'>
        trailer< '.' method_name=NAME >
        arglist=trailer< '(' args=any* ')' >
        any*
       >
       |
       power<
        NAME
        trailer< '.' NAME>*
        trailer< '.' 'sentry'>
        trailer< '.' method_name=NAME >
        arglist=trailer< '(' args=any* ')' >
        any*
       >
      )
    """

    def transform(self, node: LN, capture: Capture) -> None:
        method_name = capture["method_name"].value

        if method_name in METHOD_RENAMES:
            should_warn = False

            # the basic usage is the same, but there are a number of kwargs
            # that are totally different. we'll just warn about those.
            if capture["args"]:
                assert len(capture["args"]) == 1

                arg = capture["args"][0]
                if arg.type == syms.argument:  # captureException(foo=bar)
                    arg_name = arg.children[0]
                    if arg_name.value in ARG_RENAMES:
                        arg_name.replace(
                            Name(ARG_RENAMES[arg_name.value], prefix=arg_name.prefix)
                        )
                    else:
                        should_warn = True
                elif arg.type == syms.arglist:  # captureException(a, b, ...)
                    positional_argument_count = 0
                    for child in arg.children:
                        if child.type == syms.argument:
                            arg_name = child.children[0]
                            if arg_name.value in ARG_RENAMES:
                                arg_name.replace(
                                    Name(
                                        ARG_RENAMES[arg_name.value],
                                        prefix=arg_name.prefix,
                                    )
                                )
                            else:
                                should_warn = True
                        elif child.type == token.COMMA:
                            pass
                        else:
                            positional_argument_count += 1

                    if positional_argument_count > 1:
                        should_warn = True
                else:  # captureException("foo")
                    pass

            capture["method_name"].replace(
                Name(METHOD_RENAMES[method_name], prefix=capture["method_name"].prefix)
            )
            if not should_warn:
                return
        elif method_name.endswith("_context"):
            name, sep, _ = method_name.partition("_")
            if name in ("user", "http", "extra", "tags"):
                context_name = "request" if name == "http" else name
                args = [String(f'"{context_name}"'), Comma()]

                if capture["args"]:
                    orig_args = capture["args"]
                    assert len(orig_args) == 1
                    if orig_args[0].type == syms.arglist:
                        orig_args = capture["args"][0].children
                    args.extend(arg.clone() for arg in orig_args)

                    if not args[2].prefix:
                        args[2].prefix = " "

                capture["method_name"].replace(
                    Name("set_context", prefix=capture["method_name"].prefix)
                )
                capture["arglist"].replace(ArgList(args))
                return

        self.warn(node, "Update uses of Sentry APIs. See https://github.com/reddit/baseplate.py-upgrader/wiki/v2.0#migrating-from-raven-to-sentry-sdk")
