import collections
import re
import urllib.request

from typing import DefaultDict
from typing import List
from typing import NamedTuple
from typing import Optional


WHEEL_INDEX = "https://reddit-wheels.s3.amazonaws.com/index.html"


# https://i.imgur.com/gOPS2.png
WHEEL_RE = re.compile(
    r"^\s*<a href=\"[^\"]+\">(?P<distribution>[^-]+)-(?P<version>[^-]+)-.*</a>"
)


VERSION_RE = re.compile(r"^(?P<release>[0-9]+(?:\.[0-9]+)*)(?:\.dev(?P<dev>\d+)\+.*)?")


class WheelhouseError(Exception):
    pass


class Wheel(NamedTuple):
    name: str
    version: str


class Version(NamedTuple):
    release: str
    dev: float

    @classmethod
    def from_str(cls, version: str) -> "Version":
        m = VERSION_RE.match(version)
        if not m:
            raise ValueError(f"could not parse version {version}")

        dev = m.group("dev")
        return cls(m["release"], float(dev) if dev else float("+inf"))


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

    def get_latest_version(
        self, distribution_name: str, prefix: Optional[str] = None
    ) -> str:
        try:
            versions = self.by_distribution[distribution_name]
        except KeyError:
            raise WheelhouseError(
                f"Can't find any wheels for {repr(distribution_name)}"
            )

        if prefix:
            return str(
                max((v for v in versions if v.startswith(prefix)), key=Version.from_str)
            )
        else:
            return str(max(versions, key=Version.from_str))
