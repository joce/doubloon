"""Tests for WatchlistScreen using Textual Pilot."""

# pyright: reportPrivateUsage=none
# pylint: disable=redefined-outer-name
# pylint: disable=missing-param-doc
# ruff: noqa: PLC2801

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest
from textual.app import App
from textual.coordinate import Coordinate
from textual.worker import Worker

from appui.column_chooser_screen import ColumnChooserScreen
from appui.doubloon_config import DoubloonConfig
from appui.enhanced_data_table import EnhancedDataTable
from appui.enums import SortDirection
from appui.messages import AppExit, QuotesRefreshed, TableSortingChanged
from appui.quote_column_definitions import TICKER_COLUMN_KEY
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

    def persist_config(self) -> None:
        """Stub method to simulate config persistence."""


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
    """Lightweight stand-in for QuoteTable interactions in tests."""

    def __init__(self, keys: list[str]) -> None:
        self.cursor_row: int = 0
        self.is_ordering: bool = False
        self._keys = keys
        self.cleared_with_columns: bool | None = None
        self.columns_added: list[object] = []
        self.rows_added: list[str] = []
        self.sort_column_key: str | None = None
        self.sort_direction: object | None = None

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

    def clear(self, *, columns: bool = False) -> None:
        """Record clear calls."""

        self.cleared_with_columns = columns

    def add_enhanced_column(self, column: object) -> None:
        """Record added columns during rebuild."""

        self.columns_added.append(column)

    def add_or_update_row_data(self, key: str, quote: YQuote) -> None:  # noqa: ARG002
        """Capture rows added during rebuild."""

        self.rows_added.append(key)

    @property
    def keys(self) -> list[str]:
        """Expose current row keys for assertions."""

        return list(self._keys)


##########################
#  Binding state tests
##########################


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_mode_toggle(
    mock_yfinance: MagicMock,
) -> None:
    """Test that pressing 'o' enters ordering mode and 'Esc' exits it."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        # Get the watchlist screen
        watchlist_screen = app.watchlist_screen

        # Verify we start in default mode (not ordering)
        assert not watchlist_screen._quote_table.is_ordering
        assert watchlist_screen._binding_mode == WatchlistScreen.BM.DEFAULT

        # Press 'o' to enter ordering mode
        await pilot.press("o")

        # Verify we're now in ordering mode
        assert watchlist_screen._quote_table.is_ordering
        assert watchlist_screen._binding_mode == WatchlistScreen.BM.IN_ORDERING

        # Press 'Escape' to exit ordering mode
        await pilot.press("escape")

        # Verify we're back in default mode
        assert not watchlist_screen._quote_table.is_ordering
        assert watchlist_screen._binding_mode == WatchlistScreen.BM.DEFAULT


@pytest.mark.ui
@pytest.mark.asyncio
async def test_action_choose_columns_pushes_screen(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure the choose columns action opens the column chooser screen."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        app.push_screen_wait = AsyncMock(return_value=None)

        action = WatchlistScreen.action_choose_columns.__wrapped__  # type: ignore[attr-defined] # pylint: disable=no-member
        await action(watchlist_screen)

        app.push_screen_wait.assert_called_once()
        pushed_screen = app.push_screen_wait.call_args.args[0]
        assert isinstance(pushed_screen, ColumnChooserScreen)
        assert pushed_screen._container is watchlist_screen


@pytest.mark.ui
@pytest.mark.asyncio
async def test_get_active_keys_returns_config_columns(
    mock_yfinance: MagicMock,
) -> None:
    """Return the active keys from the watchlist config."""

    config = DoubloonConfig()
    config.watchlist.columns = ["last"]
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen

        assert watchlist_screen.get_active_keys() == ["last"]


@pytest.mark.ui
@pytest.mark.asyncio
async def test_get_frozen_keys_returns_ticker_column(
    mock_yfinance: MagicMock,
) -> None:
    """Return the ticker column key as frozen."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen

        assert watchlist_screen.get_frozen_keys() == [TICKER_COLUMN_KEY]


@pytest.mark.ui
@pytest.mark.asyncio
async def test_add_column_appends_and_updates(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure add_column appends and triggers a column refresh."""

    config = DoubloonConfig()
    config.watchlist.columns = ["last"]
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        watchlist_screen._update_columns = MagicMock()

        watchlist_screen.add_column("market_cap")

        assert config.watchlist.columns == ["last", "market_cap"]
        watchlist_screen._update_columns.assert_called_once_with()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_remove_column_updates_and_blocks_frozen(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure remove_column updates config and rejects frozen keys."""

    config = DoubloonConfig()
    config.watchlist.columns = ["last", "market_cap"]
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        watchlist_screen._update_columns = MagicMock()

        watchlist_screen.remove_column("market_cap")

        assert config.watchlist.columns == ["last"]
        watchlist_screen._update_columns.assert_called_once_with()

        with pytest.raises(ValueError):  # noqa: PT011
            watchlist_screen.remove_column(TICKER_COLUMN_KEY)


@pytest.mark.ui
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mode", "action", "expected"),
    [
        pytest.param(
            WatchlistScreen.BM.DEFAULT,
            "exit",
            True,
            id="exit-always-allowed",
        ),
        pytest.param(
            WatchlistScreen.BM.DEFAULT,
            "exit_ordering",
            False,
            id="default-blocks-exit-ordering",
        ),
        pytest.param(
            WatchlistScreen.BM.DEFAULT,
            "remove_quote",
            True,
            id="default-allows-non-exit",
        ),
        pytest.param(
            WatchlistScreen.BM.IN_ORDERING,
            "exit_ordering",
            True,
            id="ordering-allows-exit-ordering",
        ),
        pytest.param(
            WatchlistScreen.BM.IN_ORDERING,
            "remove_quote",
            False,
            id="ordering-blocks-non-exit",
        ),
    ],
)
async def test_check_action_respects_binding_mode(
    mock_yfinance: MagicMock,
    mode: WatchlistScreen.BM,
    action: str,
    *,
    expected: bool,
) -> None:
    """Verify check_action gates actions based on the binding mode."""

    app = WatchlistTestApp(config=DoubloonConfig(), yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        watchlist_screen._binding_mode = mode

        assert watchlist_screen.check_action(action, ()) is expected


@pytest.mark.ui
@pytest.mark.asyncio
async def test_delete_removes_highlighted_quote_and_updates_config(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure removal targets the focused row and updates config."""

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
        assert watchlist_screen._binding_mode == WatchlistScreen.BM.DEFAULT


@pytest.mark.ui
@pytest.mark.asyncio
async def test_delete_last_quote_resets_bindings(
    mock_yfinance: MagicMock,
) -> None:
    """Verify removing the final quote does not change binding mode."""

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
        assert watchlist_screen._binding_mode == WatchlistScreen.BM.DEFAULT


@pytest.mark.ui
@pytest.mark.asyncio
async def test_delete_binding_disabled_when_watchlist_empty(
    mock_yfinance: MagicMock,
) -> None:
    """Disable delete binding when no watchlist items remain."""

    config = DoubloonConfig()
    object.__setattr__(config.watchlist, "quotes", [])
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        watchlist_screen = app.watchlist_screen
        watchlist_screen.action_remove_quote = MagicMock()

        assert watchlist_screen.check_action("remove_quote", ()) is False

        await pilot.press("delete")

        watchlist_screen.action_remove_quote.assert_not_called()


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
    """Ensure action_add_quote appends a new symbol."""

    config = DoubloonConfig()
    object.__setattr__(config.watchlist, "quotes", [])
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        app.push_screen_wait = AsyncMock(return_value="NFLX")

        action = WatchlistScreen.action_add_quote.__wrapped__  # type: ignore[attr-defined] # pylint: disable=no-member
        await action(watchlist_screen)

        assert config.watchlist.quotes == ["NFLX"]


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

        action = WatchlistScreen.action_add_quote.__wrapped__  # type: ignore[attr-defined] # pylint: disable=no-member
        await action(watchlist_screen)

        assert config.watchlist.quotes == ["AAPL"]


@pytest.mark.ui
@pytest.mark.asyncio
async def test_action_add_quote_persists_on_new_symbol(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure adding a new symbol triggers config persistence."""

    config = DoubloonConfig()
    object.__setattr__(config.watchlist, "quotes", [])
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)
    app.persist_config = MagicMock()

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        app.push_screen_wait = AsyncMock(return_value="NFLX")

        action = WatchlistScreen.action_add_quote.__wrapped__  # type: ignore[attr-defined] # pylint: disable=no-member
        await action(watchlist_screen)

        assert config.watchlist.quotes == ["NFLX"]
        app.persist_config.assert_called_once_with()


def test_action_exit_posts_app_exit() -> None:
    """Verify exit action dispatches AppExit."""

    stub = create_autospec(WatchlistScreen)

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
async def test_action_remove_quote_persists_when_row_removed(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure removal of a valid row triggers persistence."""

    config = DoubloonConfig()
    object.__setattr__(config.watchlist, "quotes", ["AAPL", "MSFT"])
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)
    app.persist_config = MagicMock()

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        watchlist_screen._quote_table = cast(
            "QuoteTable", _StubQuoteTable(["AAPL", "MSFT"])
        )

        watchlist_screen.action_remove_quote()

        assert config.watchlist.quotes == ["MSFT"]
        app.persist_config.assert_called_once_with()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_update_columns_filters_removed_quotes(
    mock_yfinance: MagicMock,
) -> None:
    """Column rebuild should not resurrect quotes removed from the watchlist."""

    config = DoubloonConfig()
    object.__setattr__(config.watchlist, "quotes", ["AAPL", "MSFT"])
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    removed_quote = create_autospec(YQuote, symbol="AAPL")
    kept_quote = create_autospec(YQuote, symbol="MSFT")

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        watchlist_screen._quote_data = {  # type: ignore[assignment]
            "AAPL": removed_quote,
            "MSFT": kept_quote,
        }

        removal_table = _StubQuoteTable(["AAPL", "MSFT"])
        watchlist_screen._quote_table = cast("QuoteTable", removal_table)
        watchlist_screen.action_remove_quote()

        watchlist_screen._update_columns()

        assert removal_table.rows_added == ["MSFT"]


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


@pytest.mark.ui
@pytest.mark.asyncio
async def test_on_table_sorting_changed_updates_config_and_persists(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure sorting updates both config values and persistence."""

    config = DoubloonConfig()
    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)
    app.persist_config = MagicMock()

    async with app.run_test():
        watchlist_screen = app.watchlist_screen
        message = TableSortingChanged("market_cap", SortDirection.DESCENDING)

        watchlist_screen.on_table_sorting_changed(message)

        assert config.watchlist.sort_column == "market_cap"
        assert config.watchlist.sort_direction == SortDirection.DESCENDING
        app.persist_config.assert_called_once_with()
