from __future__ import annotations

import json
import logging
import operator
import re
import urllib.error
import urllib.request

from typing import Callable
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Sequence
from typing import Tuple

from .requirements import RequirementsFile


logger = logging.getLogger(__name__)


VERSION_RE = re.compile(r"^(?P<release>[0-9]+(?:\.[0-9]+)*)(?:\.dev(?P<dev>\d+)\+.*)?")
REQUIREMENT_RE = re.compile(
    r"^\s*(?P<distribution>[A-Za-z0-9_.-]+)\s*(?P<requirements>((>=|<=|==|<)[0-9ab.]+,?)+)$"
)
SPECIFIER_RE = re.compile("^(?P<op>>=|<=|==|<)(?P<version>[0-9ab.]+)$")
PRE_RELEASE_VERSION = re.compile(r"(.*?)(a|b|rc)\d+$")

OPERATORS = {">=": operator.ge, "<=": operator.le, "==": operator.eq, "<": operator.lt}


class PackageRepoError(Exception):
    pass


class Version(NamedTuple):
    release: List[int]
    dev: float

    @classmethod
    def from_str(cls, version: str) -> "Version":
        m = VERSION_RE.match(version)
        if not m:
            raise ValueError(f"could not parse version {version}")

        release = [int(c) for c in m["release"].split(".")]
        dev = m.group("dev")
        return cls(release, float(dev) if dev else float("+inf"))


class SpecifierSet(NamedTuple):
    specifiers: Sequence[Tuple[Callable[[Version, Version], bool], Version]]

    @classmethod
    def from_str(cls, requirements: str) -> "SpecifierSet":
        specifiers = []
        for specifier_text in requirements.split(","):
            m = SPECIFIER_RE.match(specifier_text)
            if not m:
                raise ValueError(f"invalid specifier {repr(specifier_text)}")
            specifiers.append((OPERATORS[m["op"]], Version.from_str(m["version"])))
        return cls(specifiers)

    def satisfied_by(self, version: Version) -> bool:
        return all(op(version, specified) for op, specified in self.specifiers)


class PackageRepo:
    @classmethod
    def new(cls) -> PackageRepo:
        return cls()

    def __init__(self) -> None:
        self._cache: Dict[str, List[str]] = {}

    def get_available_versions(self, distribution_name: str) -> List[str]:
        if distribution_name not in self._cache:
            versions = []

            try:
                with urllib.request.urlopen(
                    f"https://pypi.org/pypi/{distribution_name}/json"
                ) as f:
                    package_info = json.load(f)

                    for version, files in package_info["releases"].items():
                        if all(file["yanked"] for file in files):
                            continue
                        if PRE_RELEASE_VERSION.match(version):
                            continue
                        versions.append(version)
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise

                # unfortunate hack due to pypi issues. this package comes from the
                # wheelhouse.
                if distribution_name == "cqlmapper":
                    return ["0.2.4"]

            self._cache[distribution_name] = versions
        return self._cache[distribution_name]

    def get_latest_version(
        self, distribution_name: str, prefix: Optional[str] = None
    ) -> str:
        versions = self.get_available_versions(distribution_name)

        if not prefix or "dev" not in prefix:
            versions = [v for v in versions if "dev" not in v]

        if prefix:
            return str(
                max((v for v in versions if v.startswith(prefix)), key=Version.from_str)
            )
        else:
            return str(max(versions, key=Version.from_str))

    def ensure(
        self,
        requirements_file: RequirementsFile,
        requirement: str,
        required: bool = False,
    ) -> None:
        m = REQUIREMENT_RE.match(requirement)
        if not m:
            raise ValueError(f"invalid requirement: {repr(requirement)}")

        distribution_name = m["distribution"]
        specifiers = SpecifierSet.from_str(m["requirements"])

        current_version = None
        try:
            current_version = Version.from_str(requirements_file[distribution_name])
        except KeyError:
            if not required:
                return

        if current_version and specifiers.satisfied_by(current_version):
            return

        versions = self.get_available_versions(distribution_name)
        for version_str in sorted(versions, key=Version.from_str, reverse=True):
            version = Version.from_str(version_str)
            if specifiers.satisfied_by(version):
                logger.info(
                    "Updated %s to %s in requirements.txt",
                    distribution_name,
                    version_str,
                )
                requirements_file[distribution_name] = version_str
                break
