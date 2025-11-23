"""The quote watchlist screen."""

from __future__ import annotations

import sys
from asyncio import Lock, sleep
from enum import Enum
from typing import TYPE_CHECKING

from textual import work
from textual.binding import BindingsMap
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
        WITH_DELETE = "with_delete"
        IN_ORDERING = "in_ordering"

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

        # Widgets
        self._footer: Footer = Footer(self._doubloon_config.time_format)
        self._quote_table: QuoteTable = quote_table()

        self._quote_worker: Worker[None] | None = None
        self._yfinance_lock: Lock = Lock()

        # Bindings
        self._bindings: BindingsMap = BindingsMap()
        self._current_bindings: WatchlistScreen.BM = WatchlistScreen.BM.IN_ORDERING

        self._bindings_modes: dict[WatchlistScreen.BM, BindingsMap] = {
            WatchlistScreen.BM.DEFAULT: BindingsMap(),
            WatchlistScreen.BM.IN_ORDERING: BindingsMap(),
        }

        self._bindings_modes[WatchlistScreen.BM.DEFAULT].bind("q", "exit", "Exit")

        self._bindings_modes[WatchlistScreen.BM.DEFAULT].bind(
            "o", "order_quotes", "Change sort order"
        )
        self._bindings_modes[WatchlistScreen.BM.DEFAULT].bind(
            "insert", "add_quote", "Add quote", key_display="ins"
        )
        self._bindings_modes[WatchlistScreen.BM.DEFAULT].bind(
            "c", "choose_columns", "Columns"
        )

        # For Delete, we want the same bindings as default, plus delete
        self._bindings_modes[WatchlistScreen.BM.WITH_DELETE] = self._bindings_modes[
            WatchlistScreen.BM.DEFAULT
        ].copy()
        self._bindings_modes[WatchlistScreen.BM.WITH_DELETE].bind(
            "delete", "remove_quote", "Remove quote", key_display="del"
        )

        # For Ordering, we want to drop all default binding. No add / delete, or cursor
        # movement.
        self._bindings_modes[WatchlistScreen.BM.IN_ORDERING].bind(
            "escape", "exit_ordering", "Done", key_display="Esc"
        )

        self._switch_bindings(WatchlistScreen.BM.DEFAULT)

    @override
    def _on_mount(self, event: Mount) -> None:
        super()._on_mount(event)

        self._switch_bindings(WatchlistScreen.BM.DEFAULT)

        self._bindings = self._bindings_modes[self._current_bindings]

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

    # Actions
    @work
    async def action_add_quote(self) -> None:
        """Add a new quote to the table."""

        new_quote = await self.app.push_screen_wait(SearchScreen())
        if new_quote and new_quote not in self._config.quotes:
            self._config.quotes.append(new_quote)
            self.app.persist_config()

            self._switch_bindings(WatchlistScreen.BM.DEFAULT)

    def action_remove_quote(self) -> None:
        """Remove the selected quote from the table."""

        to_remove = self._quote_table.ordered_rows[
            self._quote_table.cursor_row
        ].key.value
        if to_remove:
            self._quote_table.remove_row_data(to_remove)
            self._config.quotes.remove(to_remove)
            self.app.persist_config()

            self._switch_bindings(WatchlistScreen.BM.DEFAULT)

    @work
    async def action_choose_columns(self) -> None:
        """Show the column chooser dialog."""

        await self.app.push_screen_wait(ColumnChooserScreen())

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

        if self._quote_worker is None or self._quote_worker.is_finished:
            self._quote_worker = self._poll_quotes()

    def on_hide(self) -> None:
        """Handle the screen being hidden."""

        if self._quote_worker and self._quote_worker.is_running:
            self._quote_worker.cancel()

    def on_quotes_refreshed(self, message: QuotesRefreshed) -> None:
        """Handle quotes refreshed messages.

        Args:
            message (QuotesRefreshed): The message.
        """

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

    # Helpers
    def _switch_bindings(self, mode: WatchlistScreen.BM) -> None:
        """Switch the bindings to the given mode.

        Args:
            mode (Watchlist.BM): The mode to switch to.
        """

        if mode == WatchlistScreen.BM.DEFAULT and len(self._config.quotes) > 0:
            mode = WatchlistScreen.BM.WITH_DELETE

        if self._current_bindings == mode:
            return
        self._current_bindings = mode
        self._bindings = self._bindings_modes[self._current_bindings]
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

        self._quote_table.sort_column_key = self._config.sort_column
        self._quote_table.sort_direction = self._config.sort_direction
