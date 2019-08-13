import textwrap

from lib2to3.refactor import RefactoringTool

import pytest


def reformat(text):
    return f"{textwrap.dedent(text)}\n\n"


class TestRefactoringTool:
    def __init__(self, fixer):
        self.refactoring_tool = RefactoringTool([fixer], {}, explicit=True)

    def refactor(self, before):
        print("INPUT: ", before)
        print(
            "PARSED: ",
            repr(self.refactoring_tool.driver.parse_string(reformat(before))),
        )
        return str(self.refactoring_tool.refactor_string(reformat(before), "<string>"))

    def refactor_and_check(self, before, expected):
        __tracebackhide__ = True

        after = self.refactor(before)
        assert reformat(expected) == after


@pytest.fixture
def make_refactorer():
    return TestRefactoringTool
