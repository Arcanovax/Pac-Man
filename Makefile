TEMP_FILE := *.egg-info build dist .pytest_cache .mypy_cache
MYPY_FLAG := --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

SRC_DIR := src
PY_FILES := $(shell find $(SRC_DIR) -name "*.py")

UV := uv
MAKEFLAGS += -s

CONFIG := config.json
MAIN_PY := pac-man.py

all: run

run:
	$(UV) run python $(MAIN_PY) $(CONFIG)

install:
	$(UV) sync

clean:
	$(RM) -rf $(TEMP_FILE)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete

debug:
	$(UV) run python -m pdb $(MAIN_PY) $(CONFIG)

lint:
	$(UV) run flake8 $(PY_FILES) $(MAIN_PY)
	$(UV) run mypy $(PY_FILES) $(MAIN_PY) $(MYPY_FLAG)

lint-strict:
	$(UV) run flake8 $(PY_FILES) $(MAIN_PY)
	$(UV) run mypy $(PY_FILES) $(MAIN_PY) --strict

build:
	$(UV) run pyinstaller --noconfirm --clean --collect-all ursina --collect-all panda3d --name pac-man --add-data "assets:assets" pac-man.py