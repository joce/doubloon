.PHONY: help tox spell spell-changed

help:
	@echo "Available commands:"
	@echo "  make tox           - Run tox (installs poetry + tox group if needed)"
	@echo "  make spell         - Run cspell on all files (installs npm + cspell if needed)"
	@echo "  make spell-changed - Run cspell only on git modified files"

tox:
	@command -v poetry >/dev/null 2>&1 || { echo >&2 "Poetry not found. Install from: https://python-poetry.org/docs/#installation"; exit 1; }
	@poetry run tox --version >/dev/null 2>&1 || { echo "Installing tox group..."; poetry install --only tox --no-root; }
	poetry run tox

spell:
	@command -v npm >/dev/null 2>&1 || { echo >&2 "npm not found. Install Node.js from: https://nodejs.org/"; exit 1; }
	@command -v cspell >/dev/null 2>&1 || { echo "Installing cspell..."; npm install -g cspell; }
	cspell . --gitignore

spell-changed:
	@command -v npm >/dev/null 2>&1 || { echo >&2 "npm not found. Install Node.js from: https://nodejs.org/"; exit 1; }
	@command -v cspell >/dev/null 2>&1 || { echo "Installing cspell..."; npm install -g cspell; }
	@git diff --name-only --diff-filter=ACMR | grep -E '\.(py|md|txt|yml|yaml)$$' | xargs -r cspell --no-must-find-files
