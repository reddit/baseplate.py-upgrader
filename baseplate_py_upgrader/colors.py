import builtins
import enum
import sys

from typing import Any
from typing import Optional
from typing import TextIO


@enum.unique
class Color(enum.Enum):
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    MAGENTA = "35"
    CYAN = "36"
    WHITE = "37"

    GRAY = "90"
    BRIGHT_WHITE = "97"

    BOLD_RED = "1;31"
    BOLD_GREEN = "1;32"
    BOLD_YELLOW = "1;33"
    BOLD_BLUE = "1;34"
    BOLD_MAGENTA = "1;35"
    BOLD_CYAN = "1;36"
    BOLD_WHITE = "1;37"

    @property
    def BOLD(self) -> "Color":
        return Color(f"1;{self.value}")

    def __str__(self) -> str:
        return str(self.value)


def colorize(message: str, color: Color) -> str:
    return f"\033[{color}m{message}\033[0m"


def print(
    *objects: Any,
    sep: str = " ",
    end: str = "\n",
    file: TextIO = sys.stdout,
    flush: bool = False,
    color: Optional[Color] = None,
) -> None:
    joined = sep.join((str(obj) for obj in objects))
    if color:
        joined = colorize(joined, color)
    return builtins.print(joined, end=end, file=file, flush=flush)
