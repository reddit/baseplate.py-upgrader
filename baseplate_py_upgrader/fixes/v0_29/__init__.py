import logging

from pathlib import Path

from ...requirements import RequirementsFile
from ...wheelhouse import Wheelhouse


def update(
    root: Path, requirements_file: RequirementsFile, wheelhouse: Wheelhouse
) -> int:
    logging.error(
        "Upgrades to 0.29 are not currently supported. See https://git.io/fj5Xc"
    )
    return 1
