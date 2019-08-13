import pytest

from baseplate_py_upgrader.wheelhouse import Version
from baseplate_py_upgrader.wheelhouse import Wheel
from baseplate_py_upgrader.wheelhouse import Wheelhouse
from baseplate_py_upgrader.wheelhouse import WheelhouseError


def test_empty_wheelhouse():
    wheelhouse = Wheelhouse([])

    with pytest.raises(WheelhouseError):
        wheelhouse.get_latest_version("baseplate")


def test_wheel_not_found():
    wheelhouse = Wheelhouse([Wheel("baseplate", "1.0")])

    with pytest.raises(WheelhouseError):
        wheelhouse.get_latest_version("missing")


def test_latest_release():
    wheelhouse = Wheelhouse(
        [
            Wheel("baseplate", "0.28"),
            Wheel("baseplate", "0.30"),
            Wheel("baseplate", "0.30.1"),
            Wheel("baseplate", "0.30.2"),
            Wheel("baseplate", "1.0"),
            Wheel("baseplate", "1.0.2"),
        ]
    )

    assert wheelhouse.get_latest_version("baseplate") == "1.0.2"


def test_latest_dev():
    wheelhouse = Wheelhouse(
        [
            Wheel("baseplate", "1.0"),
            Wheel("baseplate", "1.0.0.dev9+gdeadbeef"),
            Wheel("baseplate", "1.0.0.dev10+gcafecafe"),
        ]
    )

    assert wheelhouse.get_latest_version("baseplate") == "1.0.0.dev10+gcafecafe"


def test_parse_clean_release():
    version = Version.from_str("1.0")
    assert version.release == "1.0"
    assert version.dev == float("+inf")


def test_parse_dev_release():
    version = Version.from_str("1.0.3.dev9+gdeadbeef")
    assert version.release == "1.0.3"
    assert version.dev == 9.0
