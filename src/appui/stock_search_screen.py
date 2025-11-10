"""The stock search screen."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from textual.binding import BindingsMap
from textual.screen import Screen
from textual.widgets import Input, OptionList

from .footer import Footer

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.events import Mount

    from .doubloon_config import DoubloonConfig
    from .doubloonapp import DoubloonApp

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class StockSearchScreen(Screen[None]):
    """The watchlist screen."""

    app: DoubloonApp

    def __init__(self, config: DoubloonConfig) -> None:
        """Initialize the selector screen."""

        super().__init__()

        self._doubloon_config: DoubloonConfig = config
        self._bindings: BindingsMap = BindingsMap()

        # Widgets
        self._footer: Footer = Footer(self._doubloon_config.time_format)
        self._input: Input = Input(
            placeholder="Type symbol (e.g., AAPL, MSFT)...", classes="symbol-input"
        )
        self._option_list: OptionList = OptionList(classes="autocomplete-options")
        self._option_list.visible = False

        # Bindings
        self._bindings.bind("escape", "exit", "Exit", key_display="Esc")
        self._bindings.bind("enter", "select", "Select", key_display="Enter")
        self._bindings.bind("up", "navigate_up", "Navigate Up", key_display="↑")
        self._bindings.bind("down", "navigate_down", "Navigate Down", key_display="↓")

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

    def _update_option_list(self, text: str) -> None:
        """Update the option list with substrings of the input text."""

        if not text:
            self._option_list.clear_options()
            self._option_list.visible = False
            return

        # Generate substrings: "Cursor" -> ["C", "Cu", "Cur", "Curs", "Curso", "Cursor"]
        substrings = [text[: i + 1] for i in range(len(text))]

        # Remember current selection before clearing
        current_selection = self._option_list.highlighted

        self._option_list.visible = True
        self._option_list.clear_options()
        self._option_list.add_options(substrings)

        # Restore selection if it was valid, otherwise select first item
        if current_selection is not None and current_selection < len(substrings):
            self._option_list.highlighted = current_selection

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes to update the option list."""

        self._update_option_list(event.value)

    def action_exit(self) -> None:
        """Handle exit action - pop the screen and return to watchlist."""

        self.app.pop_screen()

    def action_select(self) -> None:
        """Handle select action - for now, just pop the screen."""

        # TODO: Implement actual symbol selection logic later
        self.app.pop_screen()

    def action_navigate_up(self) -> None:
        """Navigate up in the option list."""

        if self._option_list.option_count > 0:
            current_index = self._option_list.highlighted
            if current_index is None:
                # If nothing is highlighted, select the last item
                self._option_list.highlighted = self._option_list.option_count - 1
            elif current_index > 0:
                self._option_list.highlighted = current_index - 1

    def action_navigate_down(self) -> None:
        """Navigate down in the option list."""

        if self._option_list.option_count > 0:
            current_index = self._option_list.highlighted
            if current_index is None:
                # If nothing is highlighted, select the first item
                self._option_list.highlighted = 0
            elif current_index < self._option_list.option_count - 1:
                self._option_list.highlighted = current_index + 1
