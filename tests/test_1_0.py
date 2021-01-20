import pytest


@pytest.mark.parametrize(
    "before,expected",
    (
        ("import io", "import io"),
        ("import baseplate", "import baseplate"),
        ("import baseplate.config", "import baseplate.lib.config"),
        ("import baseplate . config", "import baseplate.lib.config"),
        (
            "import baseplate.config as whatever",
            "import baseplate.lib.config as whatever",
        ),
        (
            """
            import io, baseplate.config
            """,
            """
            import io
            import baseplate.lib.config
            """,
        ),
        (
            """
            try:
                import baseplate.config
            except ImportError:
                pass
            """,
            """
            try:
                import baseplate.lib.config
            except ImportError:
                pass
            """,
        ),
        ("import baseplate._compat", "import baseplate._compat"),
    ),
)
def test_fix_import_name(make_refactorer, before, expected):
    refactorer = make_refactorer("baseplate_py_upgrader.fixes.v1_0.fix_import_name")
    refactorer.refactor_and_check(before, expected)


@pytest.mark.parametrize(
    "before,expected",
    (
        ("from baseplate import *", "from baseplate import *"),
        (
            "from baseplate.config import Foo, Bar",
            "from baseplate.lib.config import Foo, Bar",
        ),
        ("from baseplate import config", "from baseplate.lib import config"),
        (
            """
            from baseplate import Baseplate, config
            """,
            """
            from baseplate import Baseplate
            from baseplate.lib import config
            """,
        ),
        (
            "from baseplate.secrets import SecretsStore as SHHH",
            "from baseplate.lib.secrets import SecretsStore as SHHH",
        ),
        (
            "from baseplate.secrets import Foo as One, Bar as Two",
            "from baseplate.lib.secrets import Foo as One, Bar as Two",
        ),
        (
            """
            try:
                from baseplate import Baseplate, config, core
            except ImportError:
                pass
            """,
            """
            try:
                import baseplate as core
                from baseplate import Baseplate
                from baseplate.lib import config
            except ImportError:
                pass
            """,
        ),
        (
            "from baseplate.secrets import store",
            "from baseplate.lib import secrets as store",
        ),
        ("from baseplate import core", "import baseplate as core"),
        (
            """
            from baseplate.context.memcache import (
                MonitoredMemcacheConnection,
            )
            """,
            """
            from baseplate.clients.memcache import MonitoredMemcacheConnection
            """,
        ),
        ("from baseplate._compat import range", "from baseplate._compat import range"),
    ),
)
def test_fix_import_from(make_refactorer, before, expected):
    refactorer = make_refactorer("baseplate_py_upgrader.fixes.v1_0.fix_import_from")
    refactorer.refactor_and_check(before, expected)


@pytest.mark.parametrize(
    "before,expected",
    (
        ("baseplate.config.String()", "baseplate.lib.config.String()"),
        (
            "{'key': baseplate.config.Integer()}",
            "{'key': baseplate.lib.config.Integer()}",
        ),
        (
            "(baseplate.config.Integer() * 3) + 45",
            "(baseplate.lib.config.Integer() * 3) + 45",
        ),
        ("(baseplate._compat.long())", "(baseplate._compat.long())"),
    ),
)
def test_fix_module_usage(make_refactorer, before, expected):
    refactorer = make_refactorer("baseplate_py_upgrader.fixes.v1_0.fix_module_usage")
    refactorer.refactor_and_check(before, expected)


@pytest.mark.parametrize(
    "before,expected",
    (
        (
            "'baseplate.secrets.store.SecretsStore'",
            "'baseplate.lib.secrets.SecretsStore'",
        ),
        (
            """
            '''
            This is a docstring. In it, we mention a method inline
            :py:meth:`baseplate.core.Baseplate.add_to_context`.

            We also do some documentation:

            :param baseplate.config.EndpointConfiguration endpoint: This is a param.
            '''
            """,
            """
            '''
            This is a docstring. In it, we mention a method inline
            :py:meth:`baseplate.Baseplate.add_to_context`.

            We also do some documentation:

            :param baseplate.lib.config.EndpointConfiguration endpoint: This is a param.
            '''
            """,
        ),
    ),
)
def test_fix_strings(make_refactorer, before, expected):
    refactorer = make_refactorer("baseplate_py_upgrader.fixes.v1_0.fix_strings")
    refactorer.refactor_and_check(before, expected)


@pytest.mark.parametrize(
    "input",
    (
        "span = baseplate.make_server_span(context)",
        """
            with baseplate.make_server_span(context) as span:
                pass
        """,
    ),
)
def test_fix_make_context_object(caplog, make_refactorer, input):
    refactorer = make_refactorer(
        "baseplate_py_upgrader.fixes.v1_0.fix_make_context_object"
    )
    result = refactorer.refactor(input)
    assert result, "parse failed"
    assert caplog.records
    assert caplog.records[0].levelname == "WARNING"


@pytest.mark.parametrize(
    "input",
    ("baseplate.add_to_context('cassandra', CQLMapperContextFactory(session))",),
)
def test_fix_cass_execution_profiles(caplog, make_refactorer, input):
    refactorer = make_refactorer(
        "baseplate_py_upgrader.fixes.v1_0.fix_cass_execution_profiles"
    )
    result = refactorer.refactor(input)
    assert result, "parse failed"
    assert caplog.records
    assert caplog.records[0].levelname == "WARNING"
