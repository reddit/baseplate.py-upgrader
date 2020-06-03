from pathlib import Path
from typing import Optional

from ...python_version import PythonVersion
from ...refactor import refactor_python_files
from ...requirements import RequirementsFile
from ...wheelhouse import Wheelhouse


def update(
    root: Path,
    python_version: Optional[PythonVersion],
    requirements_file: RequirementsFile,
    wheelhouse: Wheelhouse,
) -> int:
    refactor_python_files(root, __name__)
    return 0
