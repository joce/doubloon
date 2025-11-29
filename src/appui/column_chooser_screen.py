"""Screen for choosing which columns to display."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, Static

from .footer import Footer
from .quote_column_definitions import ALL_QUOTE_COLUMNS, TICKER_COLUMN_KEY

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.events import DescendantBlur, DescendantFocus, Mount

    from .doubloon_app import DoubloonApp
    from .doubloon_config import DoubloonConfig
    from .watchlist_config import WatchlistConfig

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
        self._watchlist_config: WatchlistConfig = self._doubloon_config.watchlist
        self._bindings.bind("escape", "close", "Close", key_display="Esc", show=True)
        self._footer: Footer = Footer(self._doubloon_config.time_format)
        self._ticker_label: Label = Label(
            ALL_QUOTE_COLUMNS[TICKER_COLUMN_KEY].label,
            classes="ticker-label",
        )
        self._available_list: ListView = ListView(classes="column-list available-list")
        self._active_list: ListView = ListView(classes="column-list active-list")

    @override
    def _on_mount(self, event: Mount) -> None:
        super()._on_mount(event)
        self._populate_lists()

    @override
    def compose(self) -> ComposeResult:
        content = Horizontal(classes="column-chooser-content")
        content.border_title = "\\[ Choose Columns ]"

        with (
            Static(classes="column-chooser-root"),
            content,
        ):
            with Vertical(classes="column-pane"):
                yield Label("Available Columns", classes="pane-title")
                yield self._available_list
            with Vertical(classes="column-pane"):
                yield Label("Active Columns", classes="pane-title")
                yield self._ticker_label
                yield self._active_list
        yield self._footer

    def action_close(self) -> None:
        """Dismiss the screen without making changes."""

        self.dismiss(None)

    def _on_descendant_focus(self, event: DescendantFocus) -> None:
        """Handle a descendant widget gaining focus."""
        if event.widget == self._active_list:
            self._ticker_label.add_class("focused")

    def _on_descendant_blur(self, event: DescendantBlur) -> None:
        """Handle a descendant widget losing focus."""
        if event.widget == self._active_list:
            self._ticker_label.remove_class("focused")

    def _populate_lists(self) -> None:
        """Populate the available and active column lists."""

        self._available_list.clear()
        self._active_list.clear()

        active_keys: list[str] = [
            column_key
            for column_key in self._watchlist_config.columns
            if column_key != TICKER_COLUMN_KEY
        ]
        available_keys: list[str] = [
            column_key
            for column_key in ALL_QUOTE_COLUMNS
            if column_key not in active_keys and column_key != TICKER_COLUMN_KEY
        ]

        for column_key in available_keys:
            self._available_list.append(self._build_list_item(column_key))

        for column_key in active_keys:
            self._active_list.append(self._build_list_item(column_key))

    @staticmethod
    def _build_list_item(column_key: str) -> ListItem:
        """Create a list item widget for the given column key.

        Args:
            column_key: The column key.

        Returns:
            The list item widget.
        """

        column = ALL_QUOTE_COLUMNS[column_key]
        return ListItem(Label(column.label), id=column_key)
