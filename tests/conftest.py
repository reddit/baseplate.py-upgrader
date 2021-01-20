import textwrap

from lib2to3.fixer_util import Leaf
from lib2to3.pytree import type_repr
from lib2to3.refactor import RefactoringTool

import pytest

from baseplate_py_upgrader.fixes import LN


def reformat(text):
    return f"{textwrap.dedent(text)}\n\n"


def print_node_tree(node: LN, indent=0) -> None:
    if isinstance(node, Leaf):
        print(f"{' ' * indent}{repr(node.value)}")
        return

    print(f"{' ' * indent}<{type_repr(node.type)} ", end="")

    if all(isinstance(child, Leaf) for child in node.children):
        for leaf in node.children:
            print(f"{repr(leaf.value)} ", end="")
        print(">")
    else:
        print()
        for child in node.children:
            print_node_tree(child, indent=indent + 2)
        print(f"{' ' * indent}>")


class TestRefactoringTool:
    def __init__(self, fixer):
        self.refactoring_tool = RefactoringTool([fixer], {}, explicit=True)

    def refactor(self, before):
        print("INPUT: ", before)
        print("AST: ")
        print_node_tree(self.refactoring_tool.driver.parse_string(reformat(before)))
        after = str(self.refactoring_tool.refactor_string(reformat(before), "<string>"))
        print("OUTPUT: ", after)
        return after

    def refactor_and_check(self, before, expected):
        __tracebackhide__ = True

        after = self.refactor(before)
        assert reformat(expected).rstrip("\n") == after.rstrip("\n")


@pytest.fixture
def make_refactorer():
    return TestRefactoringTool
