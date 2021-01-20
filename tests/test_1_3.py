import pytest


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
        "baseplate_py_upgrader.fixes.v1_3.fix_deprecated_wireup"
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
