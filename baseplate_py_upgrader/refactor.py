from lib2to3.main import StdoutRefactoringTool
from lib2to3.refactor import get_fixers_from_package
from pathlib import Path


def refactor_python_files(root: Path, fix_package: str) -> None:
    fixers = get_fixers_from_package(fix_package)
    options = {"print_function": True}
    refactoring_tool = StdoutRefactoringTool(
        fixers=fixers, options=options, explicit=[], nobackups=True, show_diffs=False
    )
    refactoring_tool.refactor([root], write=True)
