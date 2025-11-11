"""The quote search screen."""

from __future__ import annotations

import logging
import sys
from asyncio import Lock
from typing import TYPE_CHECKING

from textual import work
from textual.binding import BindingsMap
from textual.screen import Screen
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option

from .footer import Footer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from textual.app import ComposeResult
    from textual.events import Mount
    from textual.worker import Worker

    from calahan import YFinance, YSearchQuote, YSearchResult

    from .doubloon_config import DoubloonConfig
    from .doubloonapp import DoubloonApp

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

_LOGGER = logging.getLogger(__name__)


class QuoteSearchScreen(Screen[str]):
    """The watchlist screen."""

    app: DoubloonApp

    def __init__(self) -> None:
        """Initialize the selector screen."""

        super().__init__()

        self._doubloon_config: DoubloonConfig = self.app.config
        self._yfinance: YFinance = self.app.yfinance
        self._bindings: BindingsMap = BindingsMap()
        self._yfinance_lock: Lock = Lock()

        # Widgets
        self._footer: Footer = Footer(self._doubloon_config.time_format)
        self._input: Input = Input(
            placeholder="Type symbol (e.g., AAPL, MSFT)...", classes="symbol-input"
        )
        self._option_list: OptionList = OptionList(classes="autocomplete-options")
        self._option_list.visible = False

        # Background work state
        self._search_worker: Worker[None] | None = None
        self._latest_query: str = ""

        # Bindings
        self._bindings.bind("escape", "exit", "Exit", key_display="Esc", show=True)
        self._bindings.bind(
            "enter", "select", "Select", key_display="Enter", show=True, priority=True
        )
        self._bindings.bind("up", "navigate_up", "Navigate Up", show=False)
        self._bindings.bind("down", "navigate_down", "Navigate Down", show=False)
        self._bindings.bind("pageup", "navigate_first", "First", show=False)
        self._bindings.bind("pagedown", "navigate_last", "Last", show=False)

    @override
    def _on_mount(self, event: Mount) -> None:
        super()._on_mount(event)
        # Focus the input field when the screen is shown
        self._input.focus()

    @override
    def compose(self) -> ComposeResult:
        yield self._input
        yield self._option_list
        yield self._footer

    @override
    def _on_unmount(self) -> None:
        if self._search_worker and self._search_worker.is_running:
            self._search_worker.cancel()
        super()._on_unmount()

    @staticmethod
    def _format_quote_option(quote: YSearchQuote) -> str:
        """Return a human-friendly option label for a search quote."""

        display_name = quote.long_name or quote.short_name
        exchange = quote.exch_disp or quote.exchange
        if exchange:
            return f"{quote.symbol} — {display_name} ({exchange})"
        return f"{quote.symbol} — {display_name}"

    def _update_option_list(self, query: str, quotes: Sequence[YSearchQuote]) -> None:
        """Update the option list with the provided search options."""

        if query != self._latest_query or not query or not quotes:
            self._option_list.clear_options()
            self._option_list.visible = False
            return

        current_selection = self._option_list.highlighted

        self._option_list.visible = True
        self._option_list.clear_options()
        self._option_list.add_options(
            [Option(self._format_quote_option(quote), quote.symbol) for quote in quotes]
        )

        if current_selection is None:
            self._option_list.highlighted = 0
        elif current_selection < len(quotes):
            self._option_list.highlighted = current_selection

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes to update the option list."""

        query = event.value.strip()
        self._latest_query = query

        if self._search_worker and self._search_worker.is_running:
            self._search_worker.cancel()

        if not query:
            self._update_option_list(query, [])
            return

        self._search_worker = self._run_search(query)

    @work(exclusive=True, group="quote-search")
    async def _run_search(self, query: str) -> None:
        """Run a YFinance search for the provided query and update the UI."""

        try:
            async with self._yfinance_lock:
                result: YSearchResult = await self._yfinance.search(query)
        except Exception:
            _LOGGER.exception("Search failed for %s", query)
            self.call_after_refresh(QuoteSearchScreen._update_option_list, query, [])
            return

        self.call_after_refresh(self._update_option_list, query, result.quotes)

    def action_exit(self) -> None:
        """Handle exit action - pop the screen and return to watchlist."""

        self.dismiss(None)

    def on_input_submitted(self) -> None:
        """Select the highlighted option and return it."""

        if (
            self._option_list.highlighted is not None
            and 0 <= self._option_list.highlighted < len(self._option_list.options)
        ):
            selected_option = self._option_list.options[self._option_list.highlighted]
            self.dismiss(selected_option.id)
        else:
            self.dismiss(None)

    def action_navigate_up(self) -> None:
        """Navigate up in the option list."""

        if (
            self._option_list.highlighted is not None
            and self._option_list.highlighted > 0
        ):
            self._option_list.action_cursor_up()

    def action_navigate_down(self) -> None:
        """Navigate down in the option list."""

        if (
            self._option_list.highlighted is not None
            and self._option_list.highlighted < len(self._option_list.options) - 1
        ):
            self._option_list.action_cursor_down()

    def action_navigate_first(self) -> None:
        """Navigate to the first option in the option list."""

        self._option_list.action_first()

    def action_navigate_last(self) -> None:
        """Navigate to the last option in the option list."""

        self._option_list.action_last()
