"""Tests for WatchlistScreen using Textual Pilot."""

# pyright: reportPrivateUsage=none
# pylint: disable=redefined-outer-name
# ruff: noqa: PLC2801

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest
from textual.app import App
from textual.coordinate import Coordinate
from textual.worker import Worker

from appui.doubloon_config import DoubloonConfig
from appui.enhanced_data_table import EnhancedDataTable
from appui.enums import SortDirection
from appui.messages import AppExit, QuotesRefreshed
from appui.watchlist_screen import WatchlistScreen
from calahan.yquote import YQuote

from .helpers import get_column_header_midpoint

if TYPE_CHECKING:
    from appui.quote_table import QuoteTable
    from appui.watchlist_config import WatchlistConfig


class WatchlistTestApp(App[None]):
    """A minimal test app for testing WatchlistScreen.

    Args:
        config: The Doubloon configuration.
        yfinance: The mocked YFinance instance.
    """

    def __init__(self, config: DoubloonConfig, yfinance: MagicMock) -> None:
        """Initialize the test app.

        Args:
            config: The Doubloon configuration.
            yfinance: The mocked YFinance instance.
        """

        super().__init__()
        self.config = config
        self.yfinance = yfinance
        self._watchlist_screen: WatchlistScreen | None = None

    @property
    def watchlist_screen(self) -> WatchlistScreen:
        """Get the watchlist screen."""

        if self._watchlist_screen is None:
            self._watchlist_screen = WatchlistScreen()
        return self._watchlist_screen

    def on_mount(self) -> None:
        """Mount the watchlist screen."""
        self.push_screen(self.watchlist_screen)


@pytest.fixture
def mock_yfinance() -> MagicMock:
    """Create a mock YFinance instance.

    Returns:
        MagicMock: A mocked YFinance instance.
    """

    yfinance = MagicMock()
    yfinance.retrieve_quotes = AsyncMock(return_value=[])
    return yfinance


class _StubQuoteTable:
    """Lightweight stand-in for QuoteTable interactions in removal tests."""

    def __init__(self, keys: list[str]) -> None:
        self.cursor_row: int = 0
        self.is_ordering: bool = False
        self._keys = keys

    @property
    def ordered_rows(self) -> list[SimpleNamespace]:
        """Return ordered rows mirroring Textual's RowKey structure."""

        return [SimpleNamespace(key=SimpleNamespace(value=key)) for key in self._keys]

    def remove_row_data(self, key: str) -> None:
        """Remove the given row key.

        Args:
            key: The row key to remove.
        """

        self._keys.remove(key)

    @property
    def keys(self) -> list[str]:
        """Expose current row keys for assertions."""

        return list(self._keys)


##########################
#  Binding state tests
##########################


@pytest.mark.ui
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("configured_quotes", "expected_binding"),
    [
        pytest.param(
            [],
            WatchlistScreen.BM.DEFAULT,
            id="no-quotes",
        ),
        pytest.param(
            ["AAPL"],
            WatchlistScreen.BM.WITH_DELETE,
            id="with-quotes",
        ),
    ],
)
async def test_ordering_mode_toggle(
    mock_yfinance: MagicMock,
    configured_quotes: list[str],
    expected_binding: WatchlistScreen.BM,
) -> None:
    """Test that pressing 'o' enters ordering mode and 'Esc' exits it."""

    config = DoubloonConfig()
    # Bypass validation to allow an empty quotes list for the no-quotes scenario.
    object.__setattr__(config.watchlist, "quotes", configured_quotes.copy())

    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        # Get the watchlist screen
        watchlist_screen = app.watchlist_screen

        # Verify we start in default mode (not ordering)
        assert not watchlist_screen._quote_table.is_ordering
        assert watchlist_screen._current_bindings == expected_binding

        # Press 'o' to enter ordering mode
        await pilot.press("o")

        # Verify we're now in ordering mode
        assert watchlist_screen._quote_table.is_ordering
        assert watchlist_screen._current_bindings == WatchlistScreen.BM.IN_ORDERING

        # Press 'Escape' to exit ordering mode
        await pilot.press("escape")

        # Verify we're back in default mode
        assert not watchlist_screen._quote_table.is_ordering
        assert watchlist_screen._current_bindings == expected_binding


@pytest.mark.ui
@pytest.mark.asyncio
async def test_delete_removes_highlighted_quote_and_updates_config(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure removal targets the focused row and keeps bindings when rows remain."""

    config = DoubloonConfig()
    initial_quotes = ["AAPL", "MSFT", "TSLA"]
    object.__setattr__(config.watchlist, "quotes", initial_quotes.copy())

    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)
    watchlist: WatchlistConfig = config.watchlist

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen

        stub_table = _StubQuoteTable(initial_quotes.copy())
        stub_table.cursor_row = 1
        watchlist_screen._quote_table = cast("QuoteTable", stub_table)

        await pilot.press("delete")

        assert stub_table.keys == ["AAPL", "TSLA"]
        assert watchlist.quotes == ["AAPL", "TSLA"]
        assert watchlist_screen._current_bindings == WatchlistScreen.BM.WITH_DELETE


@pytest.mark.ui
@pytest.mark.asyncio
async def test_delete_last_quote_resets_bindings(
    mock_yfinance: MagicMock,
) -> None:
    """Verify removing the final quote clears bindings back to default."""

    config = DoubloonConfig()
    initial_quotes = ["AAPL"]
    object.__setattr__(config.watchlist, "quotes", initial_quotes.copy())

    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen

        stub_table = _StubQuoteTable(initial_quotes.copy())
        watchlist_screen._quote_table = cast("QuoteTable", stub_table)

        await pilot.press("delete")

        assert not stub_table.keys
        assert not config.watchlist.quotes
        assert watchlist_screen._current_bindings == WatchlistScreen.BM.DEFAULT


@pytest.mark.ui
@pytest.mark.asyncio
async def test_delete_key_noop_when_no_quotes(
    mock_yfinance: MagicMock,
) -> None:
    """Confirm delete shortcut is ignored once the watchlist is empty."""

    config = DoubloonConfig()
    object.__setattr__(config.watchlist, "quotes", [])

    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen

        stub_table = _StubQuoteTable([])
        watchlist_screen._quote_table = cast("QuoteTable", stub_table)

        assert watchlist_screen._current_bindings == WatchlistScreen.BM.DEFAULT

        await pilot.press("delete")

        assert not stub_table.keys
        assert not config.watchlist.quotes
        assert watchlist_screen._current_bindings == WatchlistScreen.BM.DEFAULT


##########################
#  Keyboard ordering tests
##########################


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_keyboard_highlight_tracks_sorted_column(
    mock_yfinance: MagicMock,
) -> None:
    """Verify ordering highlight activates and resets around ordering mode."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen

        quote_table = watchlist_screen._quote_table

        # Initially, no column should be highlighted
        assert quote_table._hovered_column == -1

        # The sorted column should now be highlighted
        await pilot.press("o")
        assert quote_table._hovered_column == quote_table._sort_column_idx

        # No column should be highlighted again after exiting ordering mode
        await pilot.press("escape")
        assert quote_table._hovered_column == -1


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_keyboard_navigation_respects_boundaries(
    mock_yfinance: MagicMock,
) -> None:
    """Verify arrow navigation clamps highlight between first and last columns."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen

        await pilot.press("o")

        quote_table = watchlist_screen._quote_table
        column_count = len(quote_table.columns)

        # Initial hovered column should be the first column
        assert quote_table._hovered_column == 0

        # Test left boundary by attempting to move left beyond the first column
        await pilot.press("left")
        assert quote_table._hovered_column == 0

        # Test right boundary by attempting to move right beyond the last column
        for _ in range(column_count + 1):
            await pilot.press("right")
        assert quote_table._hovered_column == column_count - 1


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_keyboard_enter_toggles_direction_on_sorted_column(
    mock_yfinance: MagicMock,
) -> None:
    """Verify Enter toggles sort direction when highlight matches sorted column."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen

        quote_table = watchlist_screen._quote_table
        assert quote_table.sort_direction == SortDirection.ASCENDING

        await pilot.press("o")

        # Press "enter" on the current column to toggle sort direction
        await pilot.press("enter")
        assert quote_table.sort_direction == SortDirection.DESCENDING

        # Press "enter" again to toggle back
        await pilot.press("enter")
        assert quote_table.sort_direction == SortDirection.ASCENDING


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_keyboard_enter_switches_sorted_column(
    mock_yfinance: MagicMock,
) -> None:
    """Verify Enter applies sorting to the newly highlighted column."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen

        quote_table = watchlist_screen._quote_table
        original_direction = quote_table.sort_direction
        original_key = quote_table.sort_column_key

        await pilot.press("o")

        # Move to a different column, but the sort should not change yet
        await pilot.press("right")
        target_column_index = quote_table._hovered_column
        target_column_key = quote_table._enhanced_columns[target_column_index].key
        assert target_column_key != original_key
        assert quote_table.sort_column_key == original_key

        await pilot.press("enter")
        assert quote_table.sort_column_key == target_column_key
        assert quote_table.sort_direction == original_direction


##########################
#  Mouse interaction tests
##########################


@pytest.mark.ui
@pytest.mark.asyncio
async def test_mouse_hover_highlights_column_when_not_ordering(
    mock_yfinance: MagicMock,
) -> None:
    """Verify mousing over column headers highlights them when NOT in ordering mode."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen
        quote_table = watchlist_screen._quote_table

        # Verify we're not in ordering mode
        assert not quote_table.is_ordering

        # Initially, no column should be highlighted
        assert quote_table._hovered_column == -1

        # Hover over the first column header
        first_column_x = get_column_header_midpoint(quote_table, 0)
        await pilot.hover("#quote-table", offset=Coordinate(first_column_x, 0))

        # The first column should now be highlighted
        assert quote_table._hovered_column == 0

        # Hover over a different column (e.g., second column)
        second_column_x = get_column_header_midpoint(quote_table, 1)
        await pilot.hover("#quote-table", offset=Coordinate(second_column_x, 0))

        # The second column should now be highlighted
        assert quote_table._hovered_column == 1


@pytest.mark.ui
@pytest.mark.asyncio
async def test_mouse_click_toggles_sort_direction_on_sorted_column_when_not_ordering(
    mock_yfinance: MagicMock,
) -> None:
    """Verify clicking current sorted column toggles direction when NOT ordering."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen
        quote_table = watchlist_screen._quote_table

        # Verify we're not in ordering mode
        assert not quote_table.is_ordering

        # Get the initial sort state
        original_sort_column = quote_table.sort_column_key
        assert quote_table.sort_direction == SortDirection.ASCENDING

        # Click on the currently sorted column header (first column)
        sorted_column_x = get_column_header_midpoint(quote_table, 0)
        await pilot.click("#quote-table", offset=Coordinate(sorted_column_x, 0))

        # Sort direction should be toggled, but column remains the same
        assert quote_table.sort_column_key == original_sort_column
        assert quote_table.sort_direction == SortDirection.DESCENDING

        # Click again to toggle back
        await pilot.click("#quote-table", offset=Coordinate(sorted_column_x, 0))

        assert quote_table.sort_column_key == original_sort_column
        assert quote_table.sort_direction == SortDirection.ASCENDING


@pytest.mark.ui
@pytest.mark.asyncio
async def test_mouse_click_switches_sorted_column_when_not_ordering(
    mock_yfinance: MagicMock,
) -> None:
    """Verify clicking a non-sorted column sets sorting when NOT ordering."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen
        quote_table = watchlist_screen._quote_table

        # Verify we're not in ordering mode
        assert not quote_table.is_ordering

        # Get the initial sort state
        original_sort_column = quote_table.sort_column_key
        original_direction = quote_table.sort_direction

        # Click on a different column header (second column)
        second_column_x = get_column_header_midpoint(quote_table, 1)
        await pilot.click("#quote-table", offset=Coordinate(second_column_x, 0))

        # Sort column should change, direction should remain the same
        new_sort_column = quote_table.sort_column_key
        assert new_sort_column != original_sort_column
        assert quote_table.sort_direction == original_direction


@pytest.mark.ui
@pytest.mark.asyncio
async def test_mouse_hover_does_not_highlight_column_when_ordering(
    mock_yfinance: MagicMock,
) -> None:
    """Verify mousing over columns does NOT highlight when IN ordering mode."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen
        quote_table = watchlist_screen._quote_table

        # Enter ordering mode
        await pilot.press("o")

        # Verify we're in ordering mode
        assert quote_table.is_ordering

        # The sorted column should be highlighted by default in ordering mode
        initial_hovered = quote_table._hovered_column
        assert initial_hovered == quote_table._sort_column_idx

        # Try to hover over a different column
        different_column_x = get_column_header_midpoint(quote_table, 1)
        await pilot.hover("#quote-table", offset=Coordinate(different_column_x, 0))

        # The hovered column should NOT change from the sorted column
        assert quote_table._hovered_column == initial_hovered


@pytest.mark.ui
@pytest.mark.asyncio
async def test_mouse_click_does_not_change_sorting_when_ordering(
    mock_yfinance: MagicMock,
) -> None:
    """Verify clicking column headers does NOT change sorting when IN ordering mode."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen
        quote_table = watchlist_screen._quote_table

        # Enter ordering mode
        await pilot.press("o")

        # Verify we're in ordering mode
        assert quote_table.is_ordering

        # Store the initial sort state
        original_sort_column = quote_table.sort_column_key
        original_direction = quote_table.sort_direction

        # Click on the currently sorted column
        sorted_column_x = get_column_header_midpoint(quote_table, 0)
        await pilot.click("#quote-table", offset=Coordinate(sorted_column_x, 0))

        # Sort should NOT change
        assert quote_table.sort_column_key == original_sort_column
        assert quote_table.sort_direction == original_direction

        # Click on a different column
        different_column_x = get_column_header_midpoint(quote_table, 1)
        await pilot.click("#quote-table", offset=Coordinate(different_column_x, 0))

        # Sort should still NOT change
        assert quote_table.sort_column_key == original_sort_column
        assert quote_table.sort_direction == original_direction


##########################
#  Search integration tests
##########################


@pytest.mark.ui
@pytest.mark.asyncio
async def test_action_add_quote_appends_symbol(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure action_add_quote appends a new symbol and refreshes bindings."""

    config = DoubloonConfig()
    object.__setattr__(config.watchlist, "quotes", [])
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        app.push_screen_wait = AsyncMock(return_value="NFLX")
        watchlist_screen._switch_bindings = MagicMock()

        action = WatchlistScreen.action_add_quote.__wrapped__  # type: ignore[attr-defined] # pylint: disable=no-member
        await action(watchlist_screen)

        assert config.watchlist.quotes == ["NFLX"]
        watchlist_screen._switch_bindings.assert_called_with(WatchlistScreen.BM.DEFAULT)


@pytest.mark.ui
@pytest.mark.asyncio
async def test_action_add_quote_ignores_existing_symbol(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure duplicates are ignored when added via search."""

    config = DoubloonConfig()
    object.__setattr__(config.watchlist, "quotes", ["AAPL"])
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        app.push_screen_wait = AsyncMock(return_value="AAPL")
        watchlist_screen._switch_bindings = MagicMock()

        action = WatchlistScreen.action_add_quote.__wrapped__  # type: ignore[attr-defined] # pylint: disable=no-member
        await action(watchlist_screen)

        assert config.watchlist.quotes == ["AAPL"]
        watchlist_screen._switch_bindings.assert_not_called()


def test_action_exit_posts_app_exit() -> None:
    """Verify exit action dispatches AppExit."""

    stub = create_autospec(WatchlistScreen, instance=True)

    WatchlistScreen.action_exit(stub)

    stub.post_message.assert_called_once()
    message = stub.post_message.call_args.args[0]
    assert isinstance(message, AppExit)


@pytest.mark.ui
@pytest.mark.asyncio
async def test_action_remove_quote_ignores_empty_key(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure remove action is a no-op when row key is empty."""

    config = DoubloonConfig()
    object.__setattr__(config.watchlist, "quotes", ["AAPL"])
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        watchlist_screen._quote_table = cast("QuoteTable", _StubQuoteTable([""]))

        watchlist_screen.action_remove_quote()

        assert config.watchlist.quotes == ["AAPL"]


@pytest.mark.ui
@pytest.mark.asyncio
async def test_on_show_starts_worker_when_idle(mock_yfinance: MagicMock) -> None:
    """Ensure on_show starts polling when worker missing."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        worker = MagicMock()
        watchlist_screen._poll_quotes = MagicMock(return_value=worker)
        watchlist_screen._quote_worker = None

        watchlist_screen.on_show()

        assert watchlist_screen._quote_worker is worker


@pytest.mark.ui
@pytest.mark.asyncio
async def test_on_show_restarts_finished_worker(mock_yfinance: MagicMock) -> None:
    """Ensure finished workers trigger a restart on show."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        finished_worker = create_autospec(Worker, is_finished=True)
        watchlist_screen._quote_worker = finished_worker
        new_worker = MagicMock()
        watchlist_screen._poll_quotes = MagicMock(return_value=new_worker)

        watchlist_screen.on_show()

        assert watchlist_screen._quote_worker is new_worker


@pytest.mark.ui
@pytest.mark.asyncio
async def test_on_show_leaves_active_worker(mock_yfinance: MagicMock) -> None:
    """Verify on_show does not restart an active worker."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        active_worker = create_autospec(
            Worker, is_finished=False, is_running=False, cancel=MagicMock()
        )
        watchlist_screen._quote_worker = active_worker
        watchlist_screen._poll_quotes = MagicMock()

        watchlist_screen.on_show()

        watchlist_screen._poll_quotes.assert_not_called()
        assert watchlist_screen._quote_worker is active_worker


@pytest.mark.ui
@pytest.mark.asyncio
async def test_on_hide_cancels_running_worker(mock_yfinance: MagicMock) -> None:
    """Verify on_hide cancels a running polling worker."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        worker = create_autospec(Worker, is_running=True, cancel=MagicMock())
        watchlist_screen._quote_worker = worker

        watchlist_screen.on_hide()

        worker.cancel.assert_called_once()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_on_hide_keeps_inactive_worker(mock_yfinance: MagicMock) -> None:
    """Ensure on_hide skips cancel when worker already stopped."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        worker = create_autospec(Worker, is_running=False, cancel=MagicMock())
        watchlist_screen._quote_worker = worker

        watchlist_screen.on_hide()

        worker.cancel.assert_not_called()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_on_unmount_cancels_running_worker(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure unmount cancels an active polling worker."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        worker = create_autospec(Worker, is_running=True, cancel=MagicMock())
        watchlist_screen._quote_worker = worker

        watchlist_screen._on_unmount()

        worker.cancel.assert_called_once()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_on_unmount_without_worker(mock_yfinance: MagicMock) -> None:
    """Ensure unmount tolerates missing workers."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        watchlist_screen._quote_worker = None
        watcher = MagicMock()
        watchlist_screen._poll_quotes = watcher

        watchlist_screen._on_unmount()

        watcher.assert_not_called()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_on_quotes_refreshed_reloads_table(mock_yfinance: MagicMock) -> None:
    """Ensure refreshed quotes clear and repopulate the table."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    quotes = [
        create_autospec(YQuote, symbol="AAPL"),
        create_autospec(YQuote, symbol="MSFT"),
    ]

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        table = create_autospec(
            EnhancedDataTable,
            quotes=quotes,
            clear=MagicMock(),
            add_or_update_row_data=MagicMock(),
        )
        watchlist_screen._quote_table = table

        watchlist_screen.on_quotes_refreshed(QuotesRefreshed(quotes))

        table.clear.assert_called_once()
        table.add_or_update_row_data.assert_any_call("AAPL", quotes[0])
        table.add_or_update_row_data.assert_any_call("MSFT", quotes[1])
