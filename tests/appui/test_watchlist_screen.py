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
    """Test that pressing 'o' enters ordering mode and 'Esc' exits it.

    Args:
        mock_yfinance: The mocked YFinance fixture.
        configured_quotes: Quotes to configure on the watchlist.
        expected_binding: The binding mode expected outside ordering.
    """
    config = DoubloonConfig()
    # Bypass validation to allow an empty quotes list for the no-quotes scenario.
    object.__setattr__(  # noqa: PLC2801
        config.watchlist, "quotes", configured_quotes[:]
    )

    app = WatchlistTestApp(config=config, yfinance=mock_yfinance)

    async with app.run_test() as pilot:
        # Get the watchlist screen
        watchlist_screen = app.watchlist_screen
        await pilot.pause()

        # Verify we start in default mode (not ordering)
        assert not watchlist_screen._quote_table.is_ordering
        assert watchlist_screen._current_bindings == expected_binding

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
        assert watchlist_screen._current_bindings == expected_binding
