"""Screen for choosing which columns to display."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Label, ListView, Static

from .footer import Footer

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from .doubloon_app import DoubloonApp
    from .doubloon_config import DoubloonConfig

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class ColumnChooserScreen(Screen[None]):
    """Dialog screen presenting available and active column lists."""

    app: DoubloonApp

    def __init__(self) -> None:
        """Initialize the column chooser dialog."""

        super().__init__()
        self._doubloon_config: DoubloonConfig = self.app.config
        self._bindings.bind("escape", "close", "Close", key_display="Esc", show=True)
        self._footer: Footer = Footer(self._doubloon_config.time_format)
        self._available_list: ListView = ListView(classes="column-list available-list")
        self._active_list: ListView = ListView(classes="column-list active-list")

    @override
    def compose(self) -> ComposeResult:
        with (
            Static(classes="column-chooser-root"),
            Horizontal(
                classes="column-chooser-content",
            ),
        ):
            with Vertical(classes="column-pane"):
                yield Label("Available Columns", classes="pane-title")
                yield self._available_list
            with Vertical(classes="column-pane"):
                yield Label("Active Columns", classes="pane-title")
                yield self._active_list
        yield self._footer

    def action_close(self) -> None:
        """Dismiss the screen without making changes."""

        self.dismiss(None)
