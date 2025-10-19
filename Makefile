.PHONY: help tox spell spell-changed coverage pre-push

help:
	@echo "Available commands:"
	@echo "  make tox           - Run tox (installs poetry + tox group if needed)"
	@echo "  make spell         - Run cspell on all files (installs npm + cspell if needed)"
	@echo "  make spell-changed - Run cspell only on git modified files"
	@echo "  make coverage      - Run pytest with coverage reports (installs dev deps if needed)"
	@echo "  make pre-push      - Run tox, coverage, and spell-changed before pushing"

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
	@echo "Checking spelling in modified files..."
	@files=$$(git diff --name-only --diff-filter=ACMR); \
	if [ -z "$$files" ]; then \
		echo "No modified files to check."; \
	else \
		echo "Files to check:"; \
		echo "$$files" | sed 's/^/  /'; \
		echo "$$files" | cspell --no-must-find-files --file-list stdin && echo "Spelling check passed!"; \
	fi

coverage:
	@command -v poetry >/dev/null 2>&1 || { echo >&2 "Poetry not found. Install from: https://python-poetry.org/docs/#installation"; exit 1; }
	@poetry run pytest --version >/dev/null 2>&1 || { echo "Installing dev dependencies..."; poetry install --with dev --no-root; }
	poetry run pytest --cov=src --cov-report=term-missing --cov-report=html

pre-push: tox coverage spell-changed
	@echo "All pre-push checks passed!"
