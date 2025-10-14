"""Main entry point for the application."""

import argparse
from pathlib import Path

from appui import DoubloonApp

parser = argparse.ArgumentParser(description="Doubloon Application")
parser.add_argument("-e", "--exp", action="store_true", help="Use experimental UI")
args = parser.parse_args()

home_dir: Path = Path("~").expanduser()
config_file_name: str = (home_dir / ".doubloon").as_posix()

app: DoubloonApp = DoubloonApp()
app.load_config(config_file_name)
app.run()
app.save_config(config_file_name)
