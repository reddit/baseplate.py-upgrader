import re

from typing import Dict
from typing import Match
from typing import Optional
from typing import Set
from typing import Union


class NameRemovedError(Exception):
    def __init__(self, name: str):
        super().__init__(
            f"{repr(name)} does not exist anymore. Remove references to it."
        )


BASEPLATE_NAME_RE = re.compile(r"(?P<name>baseplate\.(?:[A-Za-z_][A-Za-z0-9_]*\.?)+)")


class RenamedSymbols:
    def __init__(self, renames: Dict[str, Union[str, None]]):
        self.renames = renames
        self.names_seen: Set[str] = set()

    def _update_seen(self, full_name: str) -> None:
        parent_name = ""
        for name in full_name.split("."):
            if parent_name:
                parent_name = f"{parent_name}.{name}"
            else:
                parent_name = name

            self.names_seen.add(parent_name)

    def get_new_name(self, name: str) -> Optional[str]:
        """Find the most appropriate replacement for a name.

        This prefers longest (more-specific) matches over shorter ones. If the
        symbol does not need to be renamed, None is returned.

        """
        self._update_seen(name)

        for old, new in sorted(
            self.renames.items(), key=lambda i: len(i[0]), reverse=True
        ):
            if name == old or name.startswith(old + "."):
                if new is None:
                    raise NameRemovedError(old)

                try:
                    return name.replace(old, new, 1)
                except KeyError:
                    return None
        return None

    def replace_module_references(self, corpus: str) -> str:
        """Replace references to modules in a body of text."""

        def replace_name(m: Match[str]) -> str:
            old_name = m["name"]
            try:
                new_name = self.get_new_name(old_name)
            except NameRemovedError:
                new_name = None
            return new_name or old_name

        return BASEPLATE_NAME_RE.sub(replace_name, corpus, re.MULTILINE)
