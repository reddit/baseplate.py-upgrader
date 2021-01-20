import pytest


@pytest.mark.parametrize(
    "before,expected",
    (
        ("import io", "import io"),
        ("request.trace", "request.span"),
        ("context.trace", "context.span"),
        ("foo.trace", "foo.trace"),
        ("request.request_context", "request.edge_context"),
        ("context.request_context", "context.edge_context"),
        ("foo.request_context", "foo.request_context"),
        ("info.context.trace.incr_tag", "info.context.span.incr_tag"),
        ("foo.bar.baz.context.trace.incr_tag", "foo.bar.baz.context.span.incr_tag"),
    ),
)
def test_fix_context_attributes(make_refactorer, before, expected):
    refactorer = make_refactorer(
        "baseplate_py_upgrader.fixes.v2_0.fix_context_attributes"
    )
    refactorer.refactor_and_check(before, expected)


@pytest.mark.parametrize(
    "input,expected_logs",
    (
        ("baseplate = Baseplate()", ["WARNING"]),
        ("baseplate = Baseplate(app_config)", []),
        ("baseplate = Baseplate({})", []),
        ("baseplate = Baseplate({'foo': 'bar'})", []),
        ("baseplate.configure_observers(app_config)", ["WARNING"]),
        ("baseplate.configure_observers(module_name='foo')", []),
        ("baseplate.configure_observers(app_config, module_name='foo')", ["WARNING"]),
        ("baseplate.configure_observers()", []),
        ("baseplate.configure_context(app_config, {})", ["WARNING"]),
        ("baseplate.configure_context(app_config, {'foo': 'bar'})", ["WARNING"]),
        ("baseplate.configure_context(app_config, my_dict)", ["WARNING"]),
        ("baseplate.configure_context({})", []),
        ("baseplate.configure_context({'foo': 'bar'})", []),
        ("baseplate.configure_context(my_dict)", []),
    ),
)
def test_fix_deprecated_wireup(caplog, make_refactorer, input, expected_logs):
    refactorer = make_refactorer(
        "baseplate_py_upgrader.fixes.v2_0.fix_deprecated_wireup"
    )
    result = refactorer.refactor(input)
    assert result, "parse failed"

    if expected_logs:
        assert caplog.records
        for i, expected_levelname in enumerate(expected_logs):
            assert (
                caplog.records[i].levelname == expected_levelname
            ), "no warning emitted"
    else:
        assert not caplog.records, "unexpected warning emitted"


@pytest.mark.parametrize(
    "input,expected_logs",
    (
        ("baseplate.configure_observers()", []),
        ("baseplate.configure_context({})", []),
        ("baseplate.configure_logging()", ["WARNING"]),
        ("baseplate.configure_tagged_metrics(client)", ["WARNING"]),
        ("baseplate.configure_metrics(client)", ["WARNING"]),
        ("baseplate.configure_tracing(client)", ["WARNING"]),
        ("baseplate.configure_error_reporting(error_reporter)", ["WARNING"]),
    ),
)
def test_fix_observer_wireup(caplog, make_refactorer, input, expected_logs):
    refactorer = make_refactorer("baseplate_py_upgrader.fixes.v2_0.fix_observer_wireup")
    result = refactorer.refactor(input)
    assert result, "parse failed"

    if expected_logs:
        assert caplog.records
        for i, expected_levelname in enumerate(expected_logs):
            assert (
                caplog.records[i].levelname == expected_levelname
            ), "no warning emitted"
    else:
        assert not caplog.records, "unexpected warning emitted"


@pytest.mark.parametrize(
    "before,expected",
    (
        ("import io", "import io"),
        (
            "bc = BaseplateConfigurator(baseplate)",
            "bc = BaseplateConfigurator(baseplate)",
        ),
        (
            "bc = BaseplateConfigurator(baseplate, header_trust_handler=foo)",
            "bc = BaseplateConfigurator(baseplate, header_trust_handler=foo)",
        ),
        (
            "bc = BaseplateConfigurator(baseplate, trust_trace_headers=True, header_trust_handler=foo)",
            "bc = BaseplateConfigurator(baseplate, header_trust_handler=foo)",
        ),
        (
            "bc = BaseplateConfigurator(baseplate, header_trust_handler=foo, trust_trace_headers=True)",
            "bc = BaseplateConfigurator(baseplate, header_trust_handler=foo)",
        ),
        (
            "bc = BaseplateConfigurator(baseplate, header_trust_handler=foo, edge_context_factory=bar)",
            "bc = BaseplateConfigurator(baseplate, header_trust_handler=foo, edge_context_factory=bar)",
        ),
        (
            """
            from baseplate.frameworks.pyramid import BaseplateConfigurator

            bc = BaseplateConfigurator(baseplate, trust_trace_headers=True)
            """,
            """
            from baseplate.frameworks.pyramid import BaseplateConfigurator
            from baseplate.frameworks.pyramid import StaticTrustHandler

            bc = BaseplateConfigurator(baseplate, header_trust_handler=StaticTrustHandler(trust_headers=True))
            """,
        ),
        (
            """
            from baseplate.frameworks.pyramid import BaseplateConfigurator

            bc = BaseplateConfigurator(baseplate, trust_trace_headers=True, edge_context_factory=foo)
            """,
            """
            from baseplate.frameworks.pyramid import BaseplateConfigurator
            from baseplate.frameworks.pyramid import StaticTrustHandler

            bc = BaseplateConfigurator(baseplate, edge_context_factory=foo, header_trust_handler=StaticTrustHandler(trust_headers=True))
            """,
        ),
    ),
)
def test_fix_trust_trace_headers(make_refactorer, before, expected):
    refactorer = make_refactorer(
        "baseplate_py_upgrader.fixes.v2_0.fix_trust_trace_headers"
    )
    refactorer.refactor_and_check(before, expected)


@pytest.mark.parametrize(
    "before,expected",
    (
        ("ThriftConnectionPool('a')", "ThriftConnectionPool('a')"),
        (
            "ThriftConnectionPool('a', max_age=3)",
            "ThriftConnectionPool('a', max_age=3)",
        ),
        (
            "ThriftConnectionPool('a', max_age=3, max_retries=4)",
            "ThriftConnectionPool('a', max_age=3, max_connection_attempts=4)",
        ),
        (
            "ThriftConnectionPool('a', max_retries=4, max_age=3)",
            "ThriftConnectionPool('a', max_connection_attempts=4, max_age=3)",
        ),
        (
            "ThriftConnectionPool('a', max_retries=4)",
            "ThriftConnectionPool('a', max_connection_attempts=4)",
        ),
        (
            "ThriftConnectionPool('a', max_connection_attempts=4)",
            "ThriftConnectionPool('a', max_connection_attempts=4)",
        ),
        (
            "{'client': ThriftClient(MyService.Client, max_retries=3)}",
            "{'client': ThriftClient(MyService.Client, max_connection_attempts=3)}",
        ),
        (
            "thrift_pool_from_config(app_config, prefix='foo.', max_retries=3)",
            "thrift_pool_from_config(app_config, prefix='foo.', max_connection_attempts=3)",
        ),
    ),
)
def test_fix_thrift_pool(make_refactorer, before, expected):
    refactorer = make_refactorer("baseplate_py_upgrader.fixes.v2_0.fix_thrift_pool")
    refactorer.refactor_and_check(before, expected)


@pytest.mark.parametrize(
    "before,expected,expected_logs",
    (
        ("info.sentry.captureMessage()", "info.sentry.capture_message()", []),
        ("request.sentry.captureException()", "request.sentry.capture_exception()", []),
        (
            "request.sentry.captureException(exception)",
            "request.sentry.capture_exception(exception)",
            [],
        ),
        (
            "request.sentry.captureException(exc_info=exception)",
            "request.sentry.capture_exception(error=exception)",
            [],
        ),
        (
            "request.sentry.captureException(exc_info=exception, foo=bar)",
            "request.sentry.capture_exception(error=exception, foo=bar)",
            ["WARNING"],
        ),
        (
            "request.sentry.captureException(exception, foo)",
            "request.sentry.capture_exception(exception, foo)",
            ["WARNING"],
        ),
        ("request.sentry.captureMessage()", "request.sentry.capture_message()", []),
        (
            "request.sentry.captureMessage('blah')",
            "request.sentry.capture_message('blah')",
            [],
        ),
        (
            "request.sentry.captureMessage(message='blah')",
            "request.sentry.capture_message(message='blah')",
            [],
        ),
        (
            "request.sentry.captureMessage(message='blah', foo=bar)",
            "request.sentry.capture_message(message='blah', foo=bar)",
            ["WARNING"],
        ),
        (
            "request.sentry.captureMessage('message', 'foo')",
            "request.sentry.capture_message('message', 'foo')",
            ["WARNING"],
        ),
        (
            "request.sentry.captureMessage('message', extra={})",
            "request.sentry.capture_message('message', extras={})",
            [],
        ),
        (
            "request.sentry.captureMessage('message', extra={}, tags={})",
            "request.sentry.capture_message('message', extras={}, tags={})",
            [],
        ),
        (
            "request.sentry.captureBreadcrumb('blah')",
            "request.sentry.captureBreadcrumb('blah')",
            ["WARNING"],
        ),
        (
            """request.sentry.http_context({"a": "b"})""",
            """request.sentry.set_context("request", {"a": "b"})""",
            [],
        ),
        (
            """request.sentry.http_context(foo, {"a": "b"})""",
            """request.sentry.set_context("request", foo, {"a": "b"})""",
            [],
        ),
        (
            """request.sentry.extra_context({"a": "b"})""",
            """request.sentry.set_context("extra", {"a": "b"})""",
            [],
        ),
    ),
)
def test_fix_sentry(caplog, make_refactorer, before, expected, expected_logs):
    refactorer = make_refactorer("baseplate_py_upgrader.fixes.v2_0.fix_sentry")
    refactorer.refactor_and_check(before, expected)

    if expected_logs:
        assert caplog.records
        for i, expected_levelname in enumerate(expected_logs):
            assert (
                caplog.records[i].levelname == expected_levelname
            ), "no warning emitted"
    else:
        assert not caplog.records, "unexpected warning emitted"
