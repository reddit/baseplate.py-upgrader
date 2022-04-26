import collections
import configparser
import logging

from pathlib import Path
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Optional
from typing import TypeVar

from ...package_repo import PackageRepo
from ...python_version import PythonVersion
from ...refactor import refactor_python_files
from ...requirements import RequirementsFile
from ..common import RenamedSymbols


RENAMES = RenamedSymbols(
    {
        "baseplate.clients.hvac": None,
        "baseplate.observers.tracing.MAX_SIDECAR_QUEUE_SIZE": None,
        "baseplate.observers.tracing.MAX_SIDECAR_MESSAGE_SIZE": None,
        "baseplate.frameworks.queue_consumer.deprecated": None,
        "baseplate.frameworks.queue_consumer.BaseKombuConsumer": None,
        "baseplate.frameworks.queue_consumer.consume": None,
        "baseplate.frameworks.queue_consumer.Handler": None,
        "baseplate.frameworks.queue_consumer.KombuConsumer": None,
        "baseplate.frameworks.queue_consumer.WorkQueue": None,
        "baseplate.lib.crypto.MessageSigner": None,
        "baseplate.frameworks.pyramid.paste_make_app": None,
        "baseplate.frameworks.pyramid.pshell_setup": None,
        "baseplate.lib.experiments": "reddit_experiments",
        "baseplate.lib.edge_context": "reddit_edgecontext",
        "baseplate.lib.edge_context.EdgeRequestContextFactory": "reddit_edgecontext.EdgeContextFactory",
    }
)


V = TypeVar("V")


class DefaultHandlingDefaultDict(DefaultDict[str, V]):
    def __setitem__(self, key: str, value: V) -> None:
        super().__setitem__("DEFAULT", value)
        super().__setitem__(key, value)


def update_config_file(path: Path) -> None:
    additions_by_section: Dict[str, Dict[str, str]] = collections.defaultdict(dict)
    deletions_by_section: Dict[str, List[str]] = DefaultHandlingDefaultDict(list)
    sections_to_delete: List[str] = []
    renames_by_section: Dict[str, Dict[str, str]] = DefaultHandlingDefaultDict(dict)

    parser = configparser.RawConfigParser()
    with path.open() as fp:
        parser.read_file(fp)

    for section in parser.sections():
        if section.startswith("server:"):
            factory = parser[section].get("factory")
            if factory in ("baseplate.server.thrift", "baseplate.server.wsgi"):
                if "max_concurrency" in parser[section]:
                    deletions_by_section[section].append("max_concurrency")

        if section == "pshell":
            sections_to_delete.append("pshell")

        if section.startswith("app:"):
            if "server_timeout.default" not in parser[section]:
                logging.warning(
                    "[%s] in %s: No server_timeout.default. For Thrift/HTTP servers, please set one.",
                    section,
                    path,
                )

            if parser[section].get("use") == "egg:baseplate":
                deletions_by_section[section].append("use")

            deleted_sentry_options = [
                "sentry.site",
                "sentry.exclude_paths",
                "sentry.include_paths",
                "sentry.processors",
            ]
            for option in deleted_sentry_options:
                if option in parser[section]:
                    deletions_by_section[section].append(option)

            if "sentry.ignore_exceptions" in parser[section]:
                renames_by_section[section][
                    "sentry.ignore_exceptions"
                ] = "sentry.ignore_errors"

            if "sentry.additional_ignore_exceptions" in parser[section]:
                logging.warning(
                    "[%s] in %s: Deleted sentry.additional_ignore_exceptions. Use sentry.ignore_errors.",
                    section,
                    path,
                )
                deletions_by_section[section].append(
                    "sentry.additional_ignore_exceptions"
                )

            if parser[section].get("metrics.tagging", "").lower() == "true":
                logging.warning(
                    "Tagged metrics paths have changed. Update dashboards. See https://github.com/reddit/baseplate.py-upgrader/wiki/v2.0#tagged-metrics"
                )

            for opt in parser[section]:
                if opt.endswith("max_retries"):
                    prefix, *_ = opt.rpartition(".")
                    if f"{prefix}.endpoint" in parser[section]:
                        new_name = f"{prefix}.max_connection_attempts"
                        renames_by_section[section][opt] = new_name

    with path.open() as fp:
        current_section = None
        skipping_section = False
        lines = []

        for lineno, line in enumerate(fp, start=1):
            m = configparser.RawConfigParser.SECTCRE.match(line)
            if m:
                skipping_section = False
                current_section = m["header"]

                if current_section in sections_to_delete:
                    skipping_section = True
                    continue

                lines.append(line)
                for key, value in additions_by_section[current_section].items():
                    lines.append(f"{key} = {value}\n")
                continue
            elif current_section:
                if skipping_section:
                    continue

                m = configparser.RawConfigParser.OPTCRE.match(line)
                if m:
                    if m["option"] in deletions_by_section[current_section]:
                        continue

                    if m["option"] in renames_by_section[current_section]:
                        replacement = renames_by_section[current_section][m["option"]]
                        line = (
                            line[: m.start("option")]
                            + replacement
                            + line[m.end("option") :]
                        )

            lines.append(line)

    with path.open("w") as fp:
        fp.write("".join(lines))


def check_for_old_docker_builder(root: Path) -> None:
    dronefile = root / ".drone.yml"
    try:
        with dronefile.open(encoding="utf8", errors="replace") as f:
            for lineno, line in enumerate(f.readlines()):
                if "drone-plugin-docker" in line:
                    logging.warning(
                        "Line %d of .drone.yml: drone-plugin-docker does not work with Artifactory. Search 'How to Upgrade Your Baseplate Service To Use Artifactory' on Confluence for upgrade instructions.",
                        lineno,
                    )
    except IOError:
        return


def update(
    root: Path,
    python_version: Optional[PythonVersion],
    requirements_file: RequirementsFile,
    package_repo: PackageRepo,
) -> int:
    if python_version:
        if python_version < (3, 7):
            logging.error(
                "Baseplate 2.0 requires Python 3.7+. Please upgrade Python first."
            )
            return 1
    else:
        logging.warning(
            "Baseplate 2.0 requires Python 3.7+. Ensure Python is new enough."
        )

    refactor_python_files(root, __name__)

    package_repo.ensure(requirements_file, "gevent>=20.5.0")
    package_repo.ensure(requirements_file, "greenlet>=0.4.17")
    package_repo.ensure(
        requirements_file, "python-json-logger>=2.0,<3.0", required=True
    )
    package_repo.ensure(requirements_file, "reddit-v2-events>=1.21.4")

    if "baseplate.lib.experiments" in RENAMES.names_seen:
        package_repo.ensure(
            requirements_file, "reddit-experiments>=1.0.0", required=True
        )

    if "baseplate.lib.edge_context" in RENAMES.names_seen:
        package_repo.ensure(requirements_file, "cryptography>=3.0,<3.4", required=True)
        package_repo.ensure(requirements_file, "PyJWT>=2.0,<3.0", required=True)
        package_repo.ensure(
            requirements_file, "reddit-edgecontext>=1.0.0", required=True
        )

    if "thrift" in requirements_file:
        del requirements_file["thrift"]
        package_repo.ensure(
            requirements_file, "thrift-unofficial>=0.14.1,<1.0", required=True
        )

    for path in root.glob("**/*.ini"):
        if path.is_symlink():
            continue
        update_config_file(path)

    # internally, we used a different package source for docker images before
    # py3.8 that didn't have "artifactory" in their tags.
    if python_version == (3, 7):
        logging.warning(
            "Check packages install from PyPI correctly. See https://github.com/reddit/baseplate.py-upgrader/wiki/v2.0#packages-fetched-from-pypi"
        )

    if "raven" in requirements_file:
        del requirements_file["raven"]
        package_repo.ensure(requirements_file, "sentry-sdk>=0.19", required=True)

    if "cqlmapper" in requirements_file:
        del requirements_file["cqlmapper"]
        package_repo.ensure(
            requirements_file, "reddit-cqlmapper>=0.3,<1.0", required=True
        )

    logging.warning(
        "Update runtime metrics queries to use tags. See https://github.com/reddit/baseplate.py-upgrader/wiki/v2.0#tagged-runtime-metrics"
    )

    logging.warning(
        "Update OneVM manifests for compatibility. See https://github.com/reddit/baseplate.py-upgrader/wiki/v2.0#onevm-changes"
    )

    logging.warning("Add SOURCE_VERSION to Dockerfile. See https://github.com/reddit/baseplate.py-upgrader/wiki/v2.0#add-source_version-to-docker-image")

    check_for_old_docker_builder(root)

    return 0
