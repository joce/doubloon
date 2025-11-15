"""Main entry point for the application."""

from __future__ import annotations

import argparse
from pathlib import Path

from appui import DoubloonApp


def _build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""

    parser = argparse.ArgumentParser(description="Doubloon Application")
    parser.add_argument("-e", "--exp", action="store_true", help="Use experimental UI")
    return parser


def main() -> None:
    """Run the Doubloon TUI."""

    parser = _build_parser()
    parser.parse_args()

    home_dir: Path = Path("~").expanduser()
    config_file_name: str = (home_dir / ".config/doubloon/doubloon.json").as_posix()

    app: DoubloonApp = DoubloonApp()
    app.load_config(config_file_name)
    app.run()
    app.save_config(config_file_name)


if __name__ == "__main__":
    main()
