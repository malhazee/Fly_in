SHELL := /bin/bash

# Default parameters
PYTHON := uv run python
MAP ?= maps/easy/01_linear_path.txt
DELAY ?= 2.0

.PHONY: all install run visualize debug clean lint lint-strict test challenger challenger-vis help
all: run

install:
	@echo "Installing dependencies via uv..."
	uv pip install flake8 mypy

run:
	@$(PYTHON) -m src.main $(MAP)

visualize:
	@$(PYTHON) -m src.main $(MAP) -v --delay $(DELAY)

debug:
	@$(PYTHON) -m pdb src/main.py $(MAP)

clean:
	@echo "Cleaning Python caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache

lint:
	@echo "=== Running flake8 ==="
	uv run flake8 src/
	@echo "=== Running mypy (42 standard flags) ==="
	uv run mypy src/ --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@echo "=== Running flake8 ==="
	uv run flake8 src/
	@echo "=== Running mypy (--strict) ==="
	uv run mypy src/ --strict

test:
	@echo "=== Running Benchmarks on All Maps ==="
	@for map in maps/*/*.txt; do \
		echo "Testing $$map ..."; \
		$(PYTHON) -m src.main "$$map" > /dev/null && echo "  -> PASSED" || echo "  -> FAILED"; \
	done

challenger:
	@$(PYTHON) -m src.main maps/challenger/01_the_impossible_dream.txt --space-time

challenger-vis:
	@$(PYTHON) -m src.main maps/challenger/01_the_impossible_dream.txt --space-time -v --delay $(DELAY)