import logging
import re

from enum import Enum
from pathlib import Path
from typing import Iterator
from typing import NamedTuple


RESERVED_KEYWORDS = {
    "abstract",
    "alias",
    "and",
    "args",
    "as",
    "assert",
    "begin",
    "BEGIN",
    "break",
    "case",
    "catch",
    "class",
    "__CLASS__",
    "clone",
    "continue",
    "declare",
    "def",
    "default",
    "del",
    "delete",
    "__DIR__",
    "do",
    "dynamic",
    "elif",
    "else",
    "elseif",
    "elsif",
    "end",
    "END",
    "enddeclare",
    "endfor",
    "endforeach",
    "endif",
    "endswitch",
    "endwhile",
    "ensure",
    "except",
    "exec",
    "__FILE__",
    "finally",
    "for",
    "foreach",
    "from",
    "function",
    "__FUNCTION__",
    "global",
    "goto",
    "if",
    "implements",
    "import",
    "in",
    "inline",
    "instanceof",
    "interface",
    "is",
    "lambda",
    "__LINE__",
    "__METHOD__",
    "module",
    "__NAMESPACE__",
    "native",
    "new",
    "next",
    "nil",
    "not",
    "or",
    "package",
    "pass",
    "print",
    "private",
    "protected",
    "public",
    "raise",
    "redo",
    "register",
    "rescue",
    "retry",
    "return",
    "self",
    "sizeof",
    "static",
    "super",
    "switch",
    "synchronized",
    "then",
    "this",
    "throw",
    "transient",
    "try",
    "undef",
    "unless",
    "unsigned",
    "until",
    "use",
    "var",
    "virtual",
    "volatile",
    "when",
    "while",
    "with",
    "xor",
    "yield",
}


class TokenKind(Enum):
    WHITESPACE = re.compile(r"\s+")
    MULTILINE_COMMENT = re.compile(r"\/\*[^*]\/*([^*/]|[^*]\/|\*[^/])*\**\*\/")
    DOC_COMMENT = re.compile(r"\/\*\*([^*/]|[^*]\/|\*[^/])*\**\*\/")
    UNIX_COMMENT = re.compile(r"\#[^\n]*")
    COMMENT = re.compile(r"\/\/[^\n]*")
    BOOL_CONSTANT = re.compile(r"\btrue\b|\bfalse\b")
    FLOAT_CONSTANT = re.compile(
        r"[+-]?((\d+(?=\.|[Ee])(\.\d*)?)|(\.\d+))([Ee][+-]?\d+)?"
    )
    HEX_CONSTANT = re.compile(r"0x[0-9A-Fa-f]+")
    DEC_CONSTANT = re.compile(r"[+-]?[0-9]+")
    STRING_LITERAL = re.compile(r"(\"([^\\\n]|(\\.))*?\")|\'([^\\\n]|(\\.))*?\'")
    SYMBOL = re.compile(r"[:;,=*{}()<>[\]]")
    IDENTIFIER = re.compile(r"[a-zA-Z_](\.[a-zA-Z_0-9]|[a-zA-Z_0-9])*")


class Token(NamedTuple):
    kind: TokenKind
    value: str
    line: int


class ThriftError(Exception):
    pass


def read_tokens(text: str) -> Iterator[Token]:
    pos = 0
    line_no = 1

    while pos < len(text):
        for kind in TokenKind:
            m = kind.value.match(text[pos:])
            if m:
                value = m.group(0)
                line_no += value.count("\n")
                pos += m.end()

                if kind is not TokenKind.WHITESPACE:
                    yield Token(kind=kind, value=value, line=line_no)

                break
        else:
            raise ThriftError(f"Invalid Thrift IDL syntax at line {line_no}!")


def find_invalid_thrift_idl(root: Path) -> bool:
    any_errors = False
    for path in root.glob("**/*.thrift"):
        error_seen = False
        try:
            text = path.read_text("utf8")
            for token in read_tokens(text):
                if token.kind != TokenKind.IDENTIFIER:
                    continue

                if token.value == "float":
                    logging.error(
                        "Line %d of %s: The 'float' type is not supported in Apache Thrift. "
                        "See https://github.com/reddit/baseplate.py-upgrader/wiki/v0.29#float-in-thrift-idl",
                        token.line,
                        path,
                    )
                    error_seen = True
                elif token.value in RESERVED_KEYWORDS:
                    logging.error(
                        "Line %d of %s: Reserved keyword %r cannot be used for identifiers. "
                        "See https://github.com/reddit/baseplate.py-upgrader/wiki/v0.29#reserved-keywords-in-thrift-idl",
                        token.line,
                        path,
                        token.value,
                    )
                    error_seen = True
        except ThriftError as exc:
            logging.warning("Error parsing %s: %s", path, exc)

        if error_seen:
            any_errors = True

    return any_errors
