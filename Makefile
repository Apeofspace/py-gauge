SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PWD := $(CURDIR)
WORKTREE_ROOT := $(shell git rev-parse --show-toplevel 2> /dev/null)

py = $$(if [ -d $(PWD)/'venv' ]; then echo $(PWD)/"venv/bin/python3"; else echo "python3"; fi)
pip = $(py) -m pip

.PHONY: all nuitka

default: all

all:
	@echo Executing command: $(py) $(PWD)/gauge.py
	$(py) $(PWD)/gauge.py


nuitka:
	@echo Compiling with nuitka
	./venv/bin/nuitka3 --output-dir=dist --jobs=12 --standalone --onefile --remove-output --no-pyi-file --enable-plugin=tk-inter --disable-console --follow-imports client.py
