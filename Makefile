REORDER_PYTHON_IMPORTS := reorder-python-imports --py37-plus --separate-from-import --separate-relative
PYTHON_FILES = $(shell find baseplate_py_upgrader/ tests/ -name '*.py')


all:


lint:
	$(REORDER_PYTHON_IMPORTS) --diff-only $(PYTHON_FILES)
	black --diff baseplate_py_upgrader/ tests/
	flake8 baseplate_py_upgrader/ tests/
	mypy baseplate_py_upgrader/


fmt:
	$(REORDER_PYTHON_IMPORTS) --exit-zero-even-if-changed $(PYTHON_FILES)
	black baseplate_py_upgrader/ tests/


test:
	python -m pytest -v tests/


.PHONY: lint fmt test
