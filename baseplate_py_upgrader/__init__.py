import argparse
import logging
import subprocess
import sys

from pathlib import Path
from typing import Callable
from typing import Dict
from typing import Optional

from .colors import Color
from .colors import colorize
from .colors import print
from .docker import upgrade_docker_image_references
from .fixes import v0_29
from .fixes import v1_0
from .python_version import guess_python_version
from .python_version import PythonVersion
from .requirements import RequirementsFile
from .wheelhouse import Wheelhouse


def no_op_upgrade(
    root: Path,
    python_version: Optional[PythonVersion],
    requirements_file: RequirementsFile,
    wheelhouse: Wheelhouse,
) -> int:
    # nothing to do here!
    return 0


# what prefix should upgrade to what series
UPGRADES: Dict[str, str] = {
    "0.26": "0.27",
    "0.27": "0.28",
    "0.28": "0.29",
    "0.29": "0.30",
    "0.30": "1.0",
}

# this is useful if we're dealing with pre-releases temporarily
PREFIX_OVERRIDE: Dict[str, str] = {}

# packages for updating to a series
UPDATERS: Dict[
    str, Callable[[Path, Optional[PythonVersion], RequirementsFile, Wheelhouse], int]
] = {
    "0.27": no_op_upgrade,
    "0.28": no_op_upgrade,
    "0.29": v0_29.update,
    "0.30": no_op_upgrade,
    "1.0": v1_0.update,
}


class LogFormatter(logging.Formatter):
    prefixes = {
        logging.DEBUG: colorize("•", Color.BLUE),
        logging.INFO: colorize("✓", Color.GREEN.BOLD),
        logging.WARNING: colorize("▲", Color.YELLOW.BOLD),
        logging.ERROR: colorize("✘", Color.RED.BOLD),
        logging.CRITICAL: colorize("✘", Color.RED.BOLD),
    }

    def format(self, record: logging.LogRecord) -> str:
        return f" {self.prefixes[record.levelno]} {super().format(record)}"


def is_git_repo_and_clean(root: Path) -> bool:
    result = subprocess.run(["git", "status", "-s"], cwd=root, capture_output=True)
    return result.returncode == 0 and not result.stdout


def get_target_series(current_version: str) -> str:
    for prefix, target in UPGRADES.items():
        if current_version.startswith(prefix):
            return target
    raise Exception(f"No major upgrades available from {repr(current_version)}!")


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Upgrade a service to the latest Baseplate.py."
    )
    parser.add_argument(
        "source_dir",
        help="path to the source code of a service you want to upgrade",
        type=Path,
    )
    args = parser.parse_args()

    if not is_git_repo_and_clean(args.source_dir):
        print(
            f"{args.source_dir} is not a Git repository or has uncommitted changes!",
            color=Color.RED.BOLD,
        )
        print(
            "This tool makes potentially destructive changes. For safety, please commit first."
        )
        return 1

    requirements_file = RequirementsFile.from_root(args.source_dir)

    try:
        current_version = requirements_file["baseplate"]
    except KeyError:
        print("That project doesn't seem to use Baseplate.py!", color=Color.RED.BOLD)
        return 1

    python_version = guess_python_version(args.source_dir)

    wheelhouse = Wheelhouse.fetch()
    target_series = get_target_series(current_version)
    prefix = PREFIX_OVERRIDE.get(target_series, target_series)
    target_version = wheelhouse.get_latest_version("baseplate", prefix=prefix)

    print("Baseplate.py Upgrader", color=Color.CYAN.BOLD)
    print(f"Upgrading {args.source_dir}")
    if python_version:
        print(f"Python version: {'.'.join(str(v) for v in python_version)}")
    else:
        print("Failed to detect Python version.", color=Color.YELLOW.BOLD)
    print(f"Current version: v{current_version}")
    print(f"Target version: v{target_version} ({target_series} series)")
    print()

    updater = UPDATERS[target_series]
    result = updater(args.source_dir, python_version, requirements_file, wheelhouse)

    upgrade_docker_image_references(target_series, args.source_dir)

    if result == 0:
        logging.info("Updated baseplate to %s in requirements.txt", target_version)
        requirements_file["baseplate"] = target_version

        print()
        print("Automatic upgrade successful!", color=Color.CYAN.BOLD)
        print("There's more to do:", color=Color.WHITE.BOLD)
        print(" • Review the logs above.")
        print(" • Review the diff in your application.")
        print(" • Apply code formatters to clean up refactored code.")
        print(" • Thoroughly test your application.")
        print(" • Commit the changes.")

        if target_series in UPGRADES:
            print(
                "Once you're confident in this upgrade, run this tool again to upgrade further.",
                color=Color.CYAN.BOLD,
            )
    else:
        print()
        print("Upgrade failed. Please see above for details.", color=Color.RED.BOLD)

    requirements_file.write()

    return result


def main() -> None:
    formatter = LogFormatter("%(message)s")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    try:
        sys.exit(_main())
    except Exception as exc:
        print(f"Error: {exc}", color=Color.RED.BOLD)
