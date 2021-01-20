import re

from pathlib import Path
from typing import List


class RequirementsError(Exception):
    pass


class RequirementsNotFoundError(RequirementsError):
    def __init__(self, path: Path) -> None:
        super().__init__(f"Can't find requirements.txt in {path}")


REQUIREMENT_RE = re.compile(
    r"^\s*(?P<distribution>[A-Za-z0-9_.-]+)\s*==\s*(?P<version>[A-Za-z0-9+.]+)"
)


class RequirementsFile:
    @classmethod
    def from_root(cls, root: Path) -> "RequirementsFile":
        path = root / "requirements.txt"

        try:
            lines = path.read_text("utf8").splitlines()
            return cls(path, lines)
        except OSError as exc:
            raise RequirementsNotFoundError(root) from exc

    def __init__(self, path: Path, lines: List[str]):
        self.path = path
        self.lines = lines

    def __getitem__(self, distribution_name: str) -> str:
        for line in self.lines:
            m = REQUIREMENT_RE.match(line)
            if m:
                if m["distribution"].lower() == distribution_name.lower():
                    return m["version"]
        raise KeyError(f"{distribution_name} not found")

    def __setitem__(self, distribution_name: str, version: str) -> None:
        for i, line in enumerate(self.lines):
            m = REQUIREMENT_RE.match(line)
            if m:
                if m["distribution"].lower() == distribution_name.lower():
                    self.lines[i] = f"{distribution_name}=={version}"
                    return
        self.lines.append(f"{distribution_name}=={version}")

    def __delitem__(self, distribution_name: str) -> None:
        for i, line in enumerate(self.lines):
            m = REQUIREMENT_RE.match(line)
            if m:
                if m["distribution"].lower() == distribution_name.lower():
                    break
        else:
            return

        del self.lines[i]

    def __contains__(self, distribution_name: str) -> bool:
        try:
            self.__getitem__(distribution_name)
            return True
        except KeyError:
            return False

    def write(self) -> None:
        with self.path.open("w") as f:
            f.write("\n".join(self.lines) + "\n")
