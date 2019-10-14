import pytest


@pytest.mark.parametrize(
    "before,expected",
    (
        ("from baseplate import Baseplate", "from baseplate import Baseplate"),
        ("import io", "import io"),
        (
            "from baseplate.integration.thrift import BaseplateProcessorEventHandler",
            "from baseplate.integration.thrift import baseplateify_processor",
        ),
        (
            "from baseplate.integration.thrift import BaseplateProcessorEventHandler, Example",
            "from baseplate.integration.thrift import baseplateify_processor, Example",
        ),
        (
            "class Handler(MyService.ContextIface): pass",
            "class Handler(MyService.Iface): pass",
        ),
    ),
)
def test_thrift_entrypoint(make_refactorer, before, expected):
    refactorer = make_refactorer(
        "baseplate_py_upgrader.fixes.v0_29.fix_thrift_entrypoint"
    )
    refactorer.refactor_and_check(before, expected)
