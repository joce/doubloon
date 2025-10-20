"""Tests for WatchlistScreen using Textual Pilot."""

# pyright: reportPrivateUsage=none
# pylint: disable=redefined-outer-name

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from textual.app import App

from appui._watchlist_screen import WatchlistScreen
from appui.doubloon_config import DoubloonConfig


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


@pytest.fixture
def doubloon_config() -> DoubloonConfig:
    """Create a DoubloonConfig instance for testing.

    Returns:
        DoubloonConfig: A test configuration.
    """
    return DoubloonConfig()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_mode_toggle(
    doubloon_config: DoubloonConfig, mock_yfinance: MagicMock
) -> None:
    """Test that pressing 'o' enters ordering mode and 'Esc' exits it.

    Args:
        doubloon_config: The test configuration fixture.
        mock_yfinance: The mocked YFinance fixture.
    """
    app = WatchlistTestApp(config=doubloon_config, yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        # Get the watchlist screen
        watchlist_screen = app.watchlist_screen
        await pilot.pause()

        # Verify we start in default mode (not ordering)
        assert not watchlist_screen._quote_table.is_ordering
        assert watchlist_screen._current_bindings in {
            WatchlistScreen.BM.DEFAULT,
            WatchlistScreen.BM.WITH_DELETE,
        }

        # Press 'o' to enter ordering mode
        await pilot.press("o")
        await pilot.pause()

        # Verify we're now in ordering mode
        assert watchlist_screen._quote_table.is_ordering
        assert watchlist_screen._current_bindings == WatchlistScreen.BM.IN_ORDERING

        # Press 'Escape' to exit ordering mode
        await pilot.press("escape")
        await pilot.pause()

        # Verify we're back in default mode
        assert not watchlist_screen._quote_table.is_ordering
        assert watchlist_screen._current_bindings in {
            WatchlistScreen.BM.DEFAULT,
            WatchlistScreen.BM.WITH_DELETE,
        }


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_mode_bindings_change(
    doubloon_config: DoubloonConfig, mock_yfinance: MagicMock
) -> None:
    """Test that bindings change when entering and exiting ordering mode.

    Args:
        doubloon_config: The test configuration fixture.
        mock_yfinance: The mocked YFinance fixture.
    """
    app = WatchlistTestApp(config=doubloon_config, yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        # Get the watchlist screen
        watchlist_screen = app.watchlist_screen
        await pilot.pause()

        # Get initial bindings
        initial_bindings = watchlist_screen._bindings

        # Press 'o' to enter ordering mode
        await pilot.press("o")
        await pilot.pause()

        # Bindings should have changed to ordering mode bindings
        ordering_bindings = watchlist_screen._bindings
        assert ordering_bindings is not initial_bindings
        assert (
            ordering_bindings
            == watchlist_screen._bindings_modes[WatchlistScreen.BM.IN_ORDERING]
        )

        # Press 'Escape' to exit ordering mode
        await pilot.press("escape")
        await pilot.pause()

        # Bindings should be back to default/with_delete mode
        final_bindings = watchlist_screen._bindings
        assert final_bindings is not ordering_bindings
        assert final_bindings in {
            watchlist_screen._bindings_modes[WatchlistScreen.BM.DEFAULT],
            watchlist_screen._bindings_modes[WatchlistScreen.BM.WITH_DELETE],
        }
