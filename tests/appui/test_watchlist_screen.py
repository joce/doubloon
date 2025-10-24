"""Tests for WatchlistScreen using Textual Pilot."""

# pyright: reportPrivateUsage=none
# pylint: disable=redefined-outer-name

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from textual.app import App
from textual.coordinate import Coordinate

from appui._enums import SortDirection
from appui._watchlist_screen import WatchlistScreen
from appui.doubloon_config import DoubloonConfig

from .helpers import get_column_header_midpoint


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
        self.watchlist_screen = WatchlistScreen(config=config, yfinance=yfinance)

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
    object.__setattr__(  # noqa: PLC2801
        config.watchlist, "quotes", configured_quotes.copy()
    )

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
