import logging

from pathlib import Path
from typing import Optional

from ...python_version import PythonVersion
from ...requirements import RequirementsFile
from ...wheelhouse import Wheelhouse


def update(
    root: Path,
    python_version: Optional[PythonVersion],
    requirements_file: RequirementsFile,
    wheelhouse: Wheelhouse,
) -> int:
    logging.error(
        "Upgrades to 0.29 are not currently supported. See https://git.io/fj5Xc"
    )
    return 1
