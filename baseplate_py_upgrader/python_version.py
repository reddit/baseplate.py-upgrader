import re

from pathlib import Path
from typing import Optional
from typing import Tuple

from .docker import IMAGE_RE


PYTHON_REQUIRES_RE = re.compile(
    r"""python_requires=['"](>=|<=|~=)(?P<version>\d\.\d)['"]"""
)


PythonVersion = Tuple[int, int]


def _make_version_tuple(version_str: str) -> PythonVersion:
    major, sep, minor = version_str.partition(".")
    assert sep and minor
    return (int(major), int(minor))


def guess_python_version(root: Path) -> Optional[PythonVersion]:
    try:
        setup_py_text = (root / "setup.py").read_text()
        for op, version in PYTHON_REQUIRES_RE.findall(setup_py_text):
            return _make_version_tuple(version)
    except OSError:
        pass

    try:
        dockerfile_text = (root / "Dockerfile").read_text()
        for match in IMAGE_RE.findall(dockerfile_text):
            return _make_version_tuple(match[2])
    except OSError:
        pass

    try:
        dockerfile_text = (root / ".drone.yml").read_text()
        for match in IMAGE_RE.findall(dockerfile_text):
            return _make_version_tuple(match[2])
    except OSError:
        pass

    return None
