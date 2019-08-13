from lib2to3.main import StdoutRefactoringTool
from lib2to3.refactor import get_fixers_from_package
from pathlib import Path


def refactor_python_files(root: Path, fix_package: str) -> None:
    fixers = get_fixers_from_package(fix_package)
    refactoring_tool = StdoutRefactoringTool(
        fixers=fixers, options={}, explicit=[], nobackups=True, show_diffs=False
    )
    refactoring_tool.refactor([root], write=True)
