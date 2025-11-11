"""Tests for SearchScreen using Textual Pilot."""

# pyright: reportPrivateUsage=none
# pylint: disable=redefined-outer-name
# pylint: disable=missing-param-doc
# pylint: disable=missing-return-doc

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias
from unittest.mock import AsyncMock, MagicMock

import pytest
from textual.app import App

from appui.doubloon_config import DoubloonConfig
from appui.search_screen import SearchScreen
from calahan import QuoteType, YSearchQuote, YSearchResult

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from textual.pilot import Pilot

from .helpers import pilot_clear_text, pilot_press_repeat, pilot_type_text

SearchPilot: TypeAlias = Pilot[str | None]


def _quote_factory(**overrides: object) -> YSearchQuote:
    base: dict[str, object] = {
        "exchange": "NMS",
        "exchDisp": "NasdaqGS",
        "index": "quotes",
        "isYahooFinance": True,
        "quoteType": QuoteType.EQUITY,
        "score": 1.0,
        "shortname": "Example",
        "symbol": "EXAMPLE",
        "typeDisp": "Equity",
        "longname": "Example Corp",
    }
    base.update(overrides)
    return YSearchQuote.model_validate(base)


def _search_result(*quotes: YSearchQuote) -> YSearchResult:
    return YSearchResult(count=len(quotes), quotes=list(quotes))


class SearchTestApp(App[str | None]):
    """Minimal harness to exercise SearchScreen with Pilot."""

    def __init__(self, config: DoubloonConfig, yfinance: MagicMock) -> None:
        """Initialize the test app."""

        super().__init__()
        self.config = config
        self.yfinance = yfinance
        self._search_screen: SearchScreen | None = None

    @property
    def search_screen(self) -> SearchScreen:
        """Access a lazily-initialized SearchScreen instance."""

        if self._search_screen is None:
            self._search_screen = SearchScreen()
        return self._search_screen

    def on_mount(self) -> None:
        """Push the screen under test."""

        self.push_screen(self.search_screen)


@pytest.fixture
def mock_yfinance() -> MagicMock:
    """Create a YFinance stub with an async search method."""

    client = MagicMock()
    client.search = AsyncMock(return_value=_search_result())
    return client


async def _drive_search(
    pilot: SearchPilot,
    text: str,
    *,
    post_type_hook: Callable[[], Awaitable[None]] | None = None,
) -> None:
    """Type text and wait for the worker to finish."""

    await pilot_type_text(pilot, text)
    if post_type_hook:
        await post_type_hook()
    await pilot.pause()


def test_format_quote_option_prefers_long_name() -> None:
    """Ensure formatting prefers the long name when available."""

    quote = _quote_factory(symbol="AAPL", longname="Apple Inc.", shortname="Apple")

    assert SearchScreen._format_quote_option(quote) == "AAPL — Apple Inc. (NasdaqGS)"


@pytest.mark.ui
@pytest.mark.asyncio
async def test_search_screen_focuses_input_and_hides_options_on_mount(
    mock_yfinance: MagicMock,
) -> None:
    """Verify input focus and hidden options on initial mount."""

    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    async with app.run_test():
        screen = app.search_screen
        assert screen._input.has_focus
        assert not screen._option_list.visible
        assert len(screen._option_list.options) == 0


@pytest.mark.ui
@pytest.mark.asyncio
async def test_blank_query_clears_results(
    mock_yfinance: MagicMock,
) -> None:
    """Confirm blank queries clear the option list."""

    quotes = [
        _quote_factory(symbol="AA", longname="Aloca Corporation"),
        _quote_factory(symbol="AAPL", longname="Apple Inc."),
    ]
    mock_yfinance.search.return_value = _search_result(*quotes)
    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    query = "aa"

    async with app.run_test() as pilot:
        screen = app.search_screen
        await _drive_search(pilot, query)
        assert screen._option_list.visible
        assert len(screen._option_list.options) == len(quotes)

        await pilot_clear_text(pilot, len(query))

        assert not screen._latest_query
        assert not screen._option_list.visible
        assert len(screen._option_list.options) == 0


@pytest.mark.ui
@pytest.mark.asyncio
async def test_successful_search_populates_options_and_submit_returns_symbol(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure successful searches populate options and submit returns highlight."""

    quotes = [
        _quote_factory(symbol="AA", longname="Aloca Corporation"),
        _quote_factory(symbol="AAPL", longname="Apple Inc."),
    ]
    mock_yfinance.search.return_value = _search_result(*quotes)
    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    query = "aa"

    async with app.run_test() as pilot:
        screen = app.search_screen
        dismiss_spy = MagicMock()
        screen.dismiss = dismiss_spy

        await _drive_search(pilot, query)

        assert screen._option_list.visible
        assert len(screen._option_list.options) == len(quotes)
        assert screen._option_list.highlighted == 0

        await pilot.press("enter")
        dismiss_spy.assert_called_once_with("AA")


@pytest.mark.ui
@pytest.mark.asyncio
async def test_navigation_shortcuts_respect_bounds(
    mock_yfinance: MagicMock,
) -> None:
    """Exercise up/down navigation staying within bounds."""

    quotes = [
        _quote_factory(symbol="AA", longname="Aloca Corporation"),
        _quote_factory(symbol="AAPL", longname="Apple Inc."),
        _quote_factory(symbol="AAL", longname="American Airlines Group Inc."),
    ]
    mock_yfinance.search.return_value = _search_result(*quotes)
    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    async with app.run_test() as pilot:
        screen = app.search_screen
        await _drive_search(pilot, "aa")
        assert screen._option_list.highlighted == 0

        # Move down to the last option, then try to go further
        await pilot_press_repeat(pilot, "down", len(quotes) + 2)
        assert screen._option_list.highlighted == len(quotes) - 1

        # Move up to the first option, then try to go further
        await pilot_press_repeat(pilot, "up", len(quotes) + 2)
        assert screen._option_list.highlighted == 0


@pytest.mark.ui
@pytest.mark.asyncio
async def test_submit_without_selection_flashes_error(
    mock_yfinance: MagicMock,
) -> None:
    """Validate submit flashes an error and keeps the screen open."""

    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    async with app.run_test() as pilot:
        screen = app.search_screen
        dismiss_spy = MagicMock()
        screen.dismiss = dismiss_spy

        await pilot.press("enter")
        dismiss_spy.assert_not_called()
        assert screen._input.has_class("input-error")

        await pilot.pause(SearchScreen.INPUT_ERROR_FLASH_DURATION + 0.1)
        assert not screen._input.has_class("input-error")


@pytest.mark.ui
@pytest.mark.asyncio
async def test_escape_triggers_exit_action(mock_yfinance: MagicMock) -> None:
    """Check escape invokes the exit action."""

    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    async with app.run_test() as pilot:
        screen = app.search_screen
        dismiss_spy = MagicMock()
        screen.dismiss = dismiss_spy

        await pilot.press("escape")
        dismiss_spy.assert_called_once_with(None)


@pytest.mark.ui
@pytest.mark.asyncio
async def test_new_query_cancels_previous_worker(mock_yfinance: MagicMock) -> None:
    """Ensure new queries cancel any in-flight worker."""

    mock_yfinance.search.return_value = _search_result(
        _quote_factory(symbol="A", longname="Aligent Technologies, Inc."),
    )
    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    async with app.run_test() as pilot:
        screen = app.search_screen

        mock_worker = MagicMock()
        mock_worker.is_running = True
        screen._search_worker = mock_worker

        await pilot.press("a")

        mock_worker.cancel.assert_called_once()
        assert screen._search_worker is not None
        assert screen._search_worker is not mock_worker


@pytest.mark.ui
@pytest.mark.asyncio
async def test_worker_is_cancelled_on_unmount(mock_yfinance: MagicMock) -> None:
    """Verify unmount cancels the running worker."""

    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    async with app.run_test():
        screen = app.search_screen
        mock_worker = MagicMock()
        mock_worker.is_running = True
        screen._search_worker = mock_worker

        screen._on_unmount()
        mock_worker.cancel.assert_called_once()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_stale_results_are_ignored(mock_yfinance: MagicMock) -> None:
    """Confirm stale query responses are discarded."""

    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    async with app.run_test():
        screen = app.search_screen
        quotes = [_quote_factory(symbol="AAPL", longname="Apple Inc.")]
        screen._latest_query = "aa"
        screen._update_option_list("aa", quotes)
        assert screen._option_list.visible
        assert len(screen._option_list.options) == 1

        screen._latest_query = "aapl"
        screen._update_option_list("aa", quotes)

        assert not screen._option_list.visible
        assert len(screen._option_list.options) == 0


@pytest.mark.ui
@pytest.mark.asyncio
async def test_search_failure_hides_option_list(mock_yfinance: MagicMock) -> None:
    """Validate failures hide the option list."""

    quotes = [_quote_factory(symbol="AAPL", longname="Apple Inc.")]
    mock_yfinance.search.side_effect = RuntimeError("boom")
    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    async with app.run_test() as pilot:
        screen = app.search_screen
        screen._latest_query = "aa"
        screen._update_option_list("aa", quotes)
        assert screen._option_list.visible

        await pilot.press("a")

        assert not screen._option_list.visible
        assert len(screen._option_list.options) == 0


@pytest.mark.ui
@pytest.mark.asyncio
async def test_highlight_persists_when_still_in_range(
    mock_yfinance: MagicMock,
) -> None:
    """Ensure highlight persists when still within option count."""

    quotes_first = [
        _quote_factory(symbol="AA", longname="Aloca Corporation"),
        _quote_factory(symbol="AAPL", longname="Apple Inc."),
        _quote_factory(symbol="AAL", longname="American Airlines Group Inc."),
    ]
    quotes_second = [
        _quote_factory(symbol="AA", longname="Aloca Corporation"),
        _quote_factory(symbol="AAPL", longname="Apple Inc."),
        _quote_factory(symbol="AAL", longname="American Airlines Group Inc."),
        _quote_factory(symbol="AAP", longname="Advanced Auto Parts Inc."),
    ]
    app = SearchTestApp(DoubloonConfig(), mock_yfinance)
    user_highlight_index = 2

    async with app.run_test():
        screen = app.search_screen
        screen._latest_query = "a"
        screen._update_option_list("a", quotes_first)
        assert len(screen._option_list.options) == len(quotes_first)
        screen._option_list.highlighted = user_highlight_index

        screen._latest_query = "aa"
        screen._update_option_list("aa", quotes_second)

        assert screen._option_list.highlighted == user_highlight_index
        assert len(screen._option_list.options) == len(quotes_second)


@pytest.mark.ui
@pytest.mark.asyncio
async def test_navigation_first_and_last_shortcuts(mock_yfinance: MagicMock) -> None:
    """Test first/last navigation jumps to the respective edges."""

    quotes = [
        _quote_factory(symbol="AA", longname="Aloca Corporation"),
        _quote_factory(symbol="AAPL", longname="Apple Inc."),
        _quote_factory(symbol="AAL", longname="American Airlines Group Inc."),
    ]
    mock_yfinance.search.return_value = _search_result(*quotes)
    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    async with app.run_test() as pilot:
        screen = app.search_screen
        await _drive_search(pilot, "aa")

        await pilot.press("pagedown")
        assert screen._option_list.highlighted == len(quotes) - 1

        await pilot.press("pageup")
        assert screen._option_list.highlighted == 0


@pytest.mark.ui
@pytest.mark.asyncio
async def test_navigation_first_and_last_respect_bounds(
    mock_yfinance: MagicMock,
) -> None:
    """Test first/last navigation staying within bounds."""

    quotes = [
        _quote_factory(symbol="AA", longname="Aloca Corporation"),
        _quote_factory(symbol="AAPL", longname="Apple Inc."),
        _quote_factory(symbol="AAL", longname="American Airlines Group Inc."),
    ]
    mock_yfinance.search.return_value = _search_result(*quotes)
    app = SearchTestApp(DoubloonConfig(), mock_yfinance)

    async with app.run_test() as pilot:
        screen = app.search_screen
        await _drive_search(pilot, "aa")

        await pilot_press_repeat(pilot, "pagedown", 3)
        assert screen._option_list.highlighted == len(quotes) - 1

        await pilot_press_repeat(pilot, "pageup", 3)
        assert screen._option_list.highlighted == 0
