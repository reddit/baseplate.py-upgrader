from pathlib import Path
from typing import Optional

from ...package_repo import PackageRepo
from ...python_version import PythonVersion
from ...refactor import refactor_python_files
from ...requirements import RequirementsFile


def update(
    root: Path,
    python_version: Optional[PythonVersion],
    requirements_file: RequirementsFile,
    package_repo: PackageRepo,
) -> int:
    refactor_python_files(root, __name__)
    return 0
