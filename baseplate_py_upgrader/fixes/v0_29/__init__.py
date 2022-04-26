import configparser
import logging

from pathlib import Path
from typing import Dict
from typing import Optional

from ...package_repo import PackageRepo
from ...python_version import PythonVersion
from ...refactor import refactor_python_files
from ...requirements import RequirementsFile
from .thrift import find_invalid_thrift_idl


def add_max_concurrency(root: Path) -> None:
    servers: Dict[str, Optional[int]] = {}

    for path in root.glob("**/*.ini"):
        config_lines = path.read_text().splitlines()

        current_server = None
        for i, line in enumerate(config_lines):
            m = configparser.RawConfigParser.SECTCRE.match(line)
            if m:
                name = m.group("header")
                if name.startswith("server:"):
                    current_server = name
                else:
                    current_server = None
                continue

            if current_server:
                m = configparser.RawConfigParser.OPTCRE.match(line)
                if m:
                    name = m.group("option")
                    if name == "max_concurrency":
                        servers[current_server] = None
                    elif name == "factory":
                        servers[current_server] = i

        insertion_points = list(filter(None, servers.values()))
        if insertion_points:
            for line_no in sorted(insertion_points, reverse=True):
                config_lines.insert(line_no + 1, "max_concurrency = 100")

            with path.open("w") as f:
                f.write("\n".join(config_lines) + "\n")

            logging.info("Updated %s to have max_concurrency setting", path)


def fix_thrift_compiler_references(root: Path) -> None:
    for path in root.glob("**/*"):
        if not path.is_file():
            continue

        if path.stat().st_size > 1e6:
            continue

        try:
            input = path.read_text(encoding="utf8")
        except UnicodeError:
            continue

        if "thrift1" in input:
            output = input.replace("thrift1", "thrift")
            with path.open("w") as f:
                f.write(output)
            logging.info("Updated Thrift compiler references in %s", path)


def update(
    root: Path,
    python_version: Optional[PythonVersion],
    requirements_file: RequirementsFile,
    package_repo: PackageRepo,
) -> int:
    result = 0

    package_repo.ensure(requirements_file, "thrift>=0.12.0")

    refactor_python_files(root, __name__)

    add_max_concurrency(root)

    if find_invalid_thrift_idl(root):
        result = 1

    fix_thrift_compiler_references(root)

    logging.warning(
        "Verify that Thrift method calls specify all params. See https://github.com/reddit/baseplate.py-upgrader/wiki/v0.29#thrift-rpc-parameters"
    )

    return result
