import collections
import logging
import operator
import re
import urllib.request

from typing import Callable
from typing import DefaultDict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Sequence
from typing import Tuple

from .requirements import RequirementsFile


logger = logging.getLogger(__name__)


WHEEL_INDEX = "https://reddit-wheels.s3.amazonaws.com/index.html"


# https://i.imgur.com/gOPS2.png
WHEEL_RE = re.compile(
    r"^\s*<a href=\"[^\"]+\">(?P<distribution>[^-]+)-(?P<version>[^-]+)-.*</a>"
)


VERSION_RE = re.compile(r"^(?P<release>[0-9]+(?:\.[0-9]+)*)(?:\.dev(?P<dev>\d+)\+.*)?")
REQUIREMENT_RE = re.compile(
    r"^\s*(?P<distribution>[A-Za-z0-9_.-]+)\s*(?P<requirements>((>=|<=|==)[0-9.]+,?)+)$"
)
SPECIFIER_RE = re.compile("^(?P<op>>=|<=|==)(?P<version>[0-9.]+)$")


OPERATORS = {">=": operator.ge, "<=": operator.le, "==": operator.eq}


class WheelhouseError(Exception):
    pass


class Wheel(NamedTuple):
    name: str
    version: str


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


class Wheelhouse:
    @classmethod
    def fetch(cls) -> "Wheelhouse":
        wheels = []
        with urllib.request.urlopen(WHEEL_INDEX) as f:
            for line in f.read().decode("utf8").splitlines():
                m = WHEEL_RE.match(line)
                if m:
                    wheels.append(Wheel(m["distribution"].lower(), m["version"]))

        return cls(wheels)

    def __init__(self, wheels: List[Wheel]):
        by_distribution: DefaultDict[str, List[str]] = collections.defaultdict(list)
        for wheel in wheels:
            by_distribution[wheel.name].append(wheel.version)

        self.by_distribution = dict(by_distribution)

    def get_available_versions(self, distribution_name: str) -> List[str]:
        try:
            return self.by_distribution[distribution_name]
        except KeyError:
            raise WheelhouseError(
                f"Can't find any wheels for {repr(distribution_name)}"
            )

    def get_latest_version(
        self, distribution_name: str, prefix: Optional[str] = None
    ) -> str:
        versions = self.get_available_versions(distribution_name)

        if prefix:
            return str(
                max((v for v in versions if v.startswith(prefix)), key=Version.from_str)
            )
        else:
            return str(max(versions, key=Version.from_str))

    def ensure(self, requirements_file: RequirementsFile, requirement: str) -> None:
        m = REQUIREMENT_RE.match(requirement)
        if not m:
            raise ValueError(f"invalid requirement: {repr(requirement)}")

        distribution_name = m["distribution"]
        specifiers = SpecifierSet.from_str(m["requirements"])

        try:
            current_version = Version.from_str(requirements_file[distribution_name])
        except KeyError:
            return

        if specifiers.satisfied_by(current_version):
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
