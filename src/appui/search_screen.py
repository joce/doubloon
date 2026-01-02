"""The quote search screen."""

from __future__ import annotations

import logging
import sys
from asyncio import Lock
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.binding import Binding, BindingsMap, BindingType
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option

from .footer import Footer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from textual.app import ComposeResult
    from textual.events import Mount
    from textual.timer import Timer
    from textual.worker import Worker

    from calahan import YFinance, YSearchQuote, YSearchResult

    from .doubloon_app import DoubloonApp
    from .doubloon_config import DoubloonConfig

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

_LOGGER = logging.getLogger(__name__)


class SearchScreen(Screen[str]):
    """The watchlist screen."""

    app: DoubloonApp
    INPUT_ERROR_FLASH_DURATION = 0.15

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "close", "Close", key_display="esc", show=True),
        Binding("enter", "select", "Select", show=True),
        Binding("up", "navigate_up", "Navigate Up", show=False),
        Binding("down", "navigate_down", "Navigate Down", show=False),
        Binding("pageup", "navigate_first", "First", show=False),
        Binding("pagedown", "navigate_last", "Last", show=False),
    ]

    def __init__(self) -> None:
        """Initialize the selector screen."""

        super().__init__()

        self._doubloon_config: DoubloonConfig = self.app.config
        self._yfinance: YFinance = self.app.yfinance
        self._yfinance_lock = Lock()

        # Widgets
        self._footer = Footer(self._doubloon_config.time_format)

        # TODO: If / when we'll want to search something other than symbols,
        # we will to adjust the placeholder text accordingly.
        self._input = Input(
            placeholder="Type symbol (e.g., AAPL, MSFT)...", classes="symbol-input"
        )

        # disable the "select" binding from the Input so that we can use it "normally"
        # in the screen.
        new_bindings = BindingsMap()
        for key, binding in self._input._bindings:  # noqa: SLF001
            if key != "enter":
                new_bindings.bind(
                    key,
                    binding.action,
                    binding.description,
                    binding.show,
                    binding.key_display,
                    binding.priority,
                )
        self._input._bindings = new_bindings  # noqa: SLF001

        self._option_list = OptionList(classes="autocomplete-options")
        self._option_list.visible = False

        # Background work state
        self._search_worker: Worker[None] | None = None
        self._latest_query: str = ""
        self._input_error_timer: Timer | None = None

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
        self._clear_input_error_timer()
        super()._on_unmount()

    @override
    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "select":
            return True if self._input.value else None
        return super().check_action(action, parameters)

    @staticmethod
    def _format_quote_option(quote: YSearchQuote) -> str:
        """Return a human-friendly option label for a search quote.

        Args:
            quote: The YSearchQuote instance.

        Returns:
            A formatted string for display in the option list.
        """

        display_name = quote.long_name or quote.short_name
        exchange = quote.exch_disp or quote.exchange
        return f"{quote.symbol} — {display_name} ({exchange})"

    def _update_option_list(self, query: str, quotes: Sequence[YSearchQuote]) -> None:
        """Update the option list with the provided search options.

        Args:
            query: The search query that produced these results.
            quotes: The sequence of YSearchQuote results.
        """

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
        """Handle input changes to update the option list.

        Args:
            event: The Input.Changed event.
        """

        query = event.value.strip()
        if bool(self._latest_query) != bool(query):
            self.refresh_bindings()

        self._latest_query = query
        self._clear_input_error()

        if self._search_worker and self._search_worker.is_running:
            self._search_worker.cancel()

        if not query:
            self._update_option_list(query, [])
            return

        self._search_worker = self._run_search(query)

    @work(exclusive=True, group="quote-search")
    async def _run_search(self, query: str) -> None:
        """Run a YFinance search for the provided query and update the UI.

        Args:
            query: The search query.
        """

        # TODO: If / when we'll want to search something other than symbols,
        # we will to adjust the search parameters accordingly.
        try:
            async with self._yfinance_lock:
                result: YSearchResult = await self._yfinance.search(query)
        except Exception:
            _LOGGER.exception("Search failed for %s", query)
            self.call_after_refresh(self._update_option_list, query, [])
            return

        self.call_after_refresh(self._update_option_list, query, result.quotes)

    def action_close(self) -> None:
        """Handle close action - pop the screen and return to watchlist."""

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
            self._flash_input_error()

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

    def _flash_input_error(self) -> None:
        """Flash the input border to indicate invalid submission."""

        self._input.add_class("input-error")
        self._clear_input_error_timer()
        self._input_error_timer = self.set_timer(
            SearchScreen.INPUT_ERROR_FLASH_DURATION,
            self._clear_input_error,
        )
        self.app.bell()

    def _clear_input_error(self) -> None:
        """Remove the input error class and stop the timer."""

        self._input.remove_class("input-error")
        self._clear_input_error_timer()

    def _clear_input_error_timer(self) -> None:
        """Stop the active input error timer if present."""

        if self._input_error_timer is not None:
            self._input_error_timer.stop()
        self._input_error_timer = None
