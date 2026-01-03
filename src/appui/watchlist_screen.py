"""The quote watchlist screen."""

from __future__ import annotations

import sys
from asyncio import Lock, sleep
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.binding import Binding, BindingType
from textual.screen import Screen

from .column_chooser_screen import ColumnChooserScreen
from .footer import Footer
from .messages import AppExit, QuotesRefreshed, TableSortingChanged
from .quote_column_definitions import ALL_QUOTE_COLUMNS, TICKER_COLUMN_KEY
from .quote_table import QuoteColumn, quote_table
from .search_screen import SearchScreen

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.events import Mount
    from textual.worker import Worker

    from calahan import YFinance, YQuote

    from .doubloon_app import DoubloonApp
    from .doubloon_config import DoubloonConfig
    from .quote_table import QuoteTable
    from .watchlist_config import WatchlistConfig

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class WatchlistScreen(Screen[None]):
    """The watchlist screen."""

    app: DoubloonApp

    class BM(Enum):
        """The binding mode enum for the quote table."""

        DEFAULT = "default"
        IN_ORDERING = "in_ordering"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl-q", "exit", "Exit", key_display="^q"),
        Binding("escape", "exit_ordering", "Done", key_display="esc"),
        Binding("o", "order_quotes", "Change sort order"),
        Binding("insert", "add_quote", "Add quote", key_display="ins"),
        Binding("c", "choose_columns", "Columns"),
        Binding("delete", "remove_quote", "Remove quote", key_display="del"),
    ]

    def __init__(self) -> None:
        """Initialize the watchlist screen."""

        super().__init__()

        # Params
        self._doubloon_config: DoubloonConfig = self.app.config
        # convenience alias
        self._config: WatchlistConfig = self._doubloon_config.watchlist
        self._yfinance: YFinance = self.app.yfinance

        # Data
        self._columns: list[QuoteColumn] = []
        self._quote_data: dict[str, YQuote] = {}

        # Widgets
        self._footer = Footer(self._doubloon_config.time_format)
        self._quote_table: QuoteTable = quote_table()

        self._quote_worker: Worker[None] | None = None
        self._yfinance_lock = Lock()

        # Bindings
        self._binding_mode = WatchlistScreen.BM.DEFAULT

    @override
    def _on_mount(self, event: Mount) -> None:
        super()._on_mount(event)

        self._switch_bindings(WatchlistScreen.BM.DEFAULT)
        self._update_columns()

    @override
    def _on_unmount(self) -> None:
        if self._quote_worker and self._quote_worker.is_running:
            self._quote_worker.cancel()
        super()._on_unmount()

    @override
    def compose(self) -> ComposeResult:
        yield self._quote_table
        yield self._footer

    @override
    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "exit":
            return True
        if action == "remove_quote" and not self._config.quotes:
            return False
        if self._binding_mode == WatchlistScreen.BM.DEFAULT:
            return action != "exit_ordering"
        if self._binding_mode == WatchlistScreen.BM.IN_ORDERING:
            return action == "exit_ordering"
        return super().check_action(action, parameters)

    # Actions
    @work
    async def action_add_quote(self) -> None:
        """Add a new quote to the table."""

        new_quote = await self.app.push_screen_wait(SearchScreen())
        if new_quote and new_quote not in self._config.quotes:
            self._config.quotes.append(new_quote)
            self.app.persist_config()
            self._force_restart_quote_worker()
            self.refresh_bindings()

    def action_remove_quote(self) -> None:
        """Remove the selected quote from the table."""

        try:
            to_remove = self._quote_table.ordered_rows[
                self._quote_table.cursor_row
            ].key.value
        except IndexError:
            return
        if to_remove:
            self._quote_table.remove_row_data(to_remove)
            self._config.quotes.remove(to_remove)
            self._quote_data.pop(to_remove, None)
            self.app.persist_config()
            self.refresh_bindings()

    @work
    async def action_choose_columns(self) -> None:
        """Show the column chooser dialog."""

        await self.app.push_screen_wait(
            ColumnChooserScreen(
                registry=ALL_QUOTE_COLUMNS,  # dict satisfies ColumnRegistry protocol
                container=self,  # WatchlistScreen implements ColumnContainer
            )
        )

    def action_order_quotes(self) -> None:
        """Order the quotes in the table."""

        self._quote_table.is_ordering = True
        self._switch_bindings(WatchlistScreen.BM.IN_ORDERING)

    def action_exit_ordering(self) -> None:
        """Exit the ordering mode."""

        self._quote_table.is_ordering = False
        self._switch_bindings(WatchlistScreen.BM.DEFAULT)

    def action_exit(self) -> None:
        """Handle exit actions."""

        self.post_message(AppExit())

    # Message handlers
    def on_table_sorting_changed(self, message: TableSortingChanged) -> None:
        """Handle table sorting changed messages.

        Args:
            message (TableSortingChanged): The message.
        """

        self._config.sort_column = message.column_key
        self._config.sort_direction = message.direction
        self.app.persist_config()

    def on_show(self) -> None:
        """Handle the screen being shown."""

        self._start_quote_worker()

    def on_hide(self) -> None:
        """Handle the screen being hidden."""

        self._cancel_quote_worker()

    def on_quotes_refreshed(self, message: QuotesRefreshed) -> None:
        """Handle quotes refreshed messages.

        Args:
            message (QuotesRefreshed): The message.
        """

        # Update cache first
        for quote in message.quotes:
            self._quote_data[quote.symbol] = quote

        # Update table
        self._quote_table.clear()
        for quote in message.quotes:
            self._quote_table.add_or_update_row_data(quote.symbol, quote)

    # Workers
    @work(exclusive=True, group="watchlist-quotes")
    async def _poll_quotes(self) -> None:
        """Poll quotes periodically and update the table."""

        delay = 10  # max(1, self._config.query_frequency)
        while True:
            try:
                quotes: list[YQuote] = []
                if self._config.quotes:
                    async with self._yfinance_lock:
                        quotes = await self._yfinance.retrieve_quotes(
                            self._config.quotes
                        )
                    self.post_message(QuotesRefreshed(quotes))
            finally:
                await sleep(delay)

    # ColumnContainer protocol implementation
    def get_active_keys(self) -> list[str]:
        """Get ordered list of currently active column keys.

        Returns:
            List of active column keys
        """
        return self._config.columns

    def get_frozen_keys(self) -> list[str]:  # noqa: PLR6301
        """Get list of column keys that cannot be removed.

        Returns:
            List containing the ticker column key
        """
        return [TICKER_COLUMN_KEY]

    def add_column(self, key: str) -> None:
        """Add a column to the active list and update the screen.

        Args:
            key: The column key to add
        """
        if key not in self._config.columns:
            self._config.columns.append(key)
            self._update_columns()

    def remove_column(self, key: str) -> None:
        """Remove a column from the active list and update the screen.

        Args:
            key: The column key to remove

        Raises:
            ValueError: If the column is frozen
        """
        if key in self.get_frozen_keys():
            msg = f"Cannot remove frozen column: {key}"
            raise ValueError(msg)
        self._config.columns.remove(key)
        self._update_columns()

    def move_column(self, key: str, new_index: int) -> None:
        """Move an active column to a new position and update the screen.

        Args:
            key: The column key to move
            new_index: The destination index within the active columns list

        Raises:
            ValueError: If the column is not active or the index is invalid
        """
        if key not in self._config.columns:
            msg = f"Cannot move inactive column: {key}"
            raise ValueError(msg)
        if new_index < 0 or new_index >= len(self._config.columns):
            msg = f"Invalid column index: {new_index}"
            raise ValueError(msg)

        current_index = self._config.columns.index(key)
        if current_index == new_index:
            return

        self._config.columns.pop(current_index)
        self._config.columns.insert(new_index, key)
        self._update_columns()

    # Helpers
    def _switch_bindings(self, mode: WatchlistScreen.BM) -> None:
        """Switch the bindings to the given mode.

        Args:
            mode (Watchlist.BM): The mode to switch to.
        """

        if self._binding_mode == mode:
            return
        self._binding_mode = mode
        self.refresh_bindings()

    def _update_columns(self) -> None:
        """Update the columns in the quote table based on the configuration."""

        self._columns = [
            ALL_QUOTE_COLUMNS[TICKER_COLUMN_KEY],
            *(
                ALL_QUOTE_COLUMNS[column]
                for column in self._config.columns
                if column != TICKER_COLUMN_KEY
            ),
        ]

        self._quote_table.clear(columns=True)
        for column in self._columns:
            self._quote_table.add_enhanced_column(column)

        # Repopulate from cache
        for symbol, quote in self._quote_data.items():
            self._quote_table.add_or_update_row_data(symbol, quote)

        self._quote_table.sort_column_key = self._config.sort_column
        self._quote_table.sort_direction = self._config.sort_direction

    def _cancel_quote_worker(self) -> None:
        if self._quote_worker and self._quote_worker.is_running:
            self._quote_worker.cancel()
        self._quote_worker = None

    def _start_quote_worker(self) -> None:
        if self._quote_worker is None or self._quote_worker.is_finished:
            self._quote_worker = self._poll_quotes()

    def _force_restart_quote_worker(self) -> None:
        self._cancel_quote_worker()
        self._start_quote_worker()
