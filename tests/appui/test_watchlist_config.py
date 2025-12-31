"""Tests for WatchlistConfig model behavior."""

# pyright: reportPrivateUsage=none

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from textual.app import App

from appui.doubloon_config import DoubloonConfig
from appui.enums import SortDirection
from appui.watchlist_config import WatchlistConfig
from appui.watchlist_screen import WatchlistScreen


class _MoveColumnTestApp(App[None]):
    """Minimal app wrapper for WatchlistScreen move_column tests."""

    def __init__(self, config: DoubloonConfig) -> None:
        super().__init__()
        self.config = config
        self.yfinance = MagicMock()


class _MoveColumnTestScreen(WatchlistScreen):
    """WatchlistScreen variant that records column update calls."""

    def __init__(self) -> None:
        super().__init__()
        self.update_calls: int = 0

    def _update_columns(self) -> None:
        self.update_calls += 1


def test_default_values() -> None:
    """Defaults mirror manual impl and include ticker implicitly."""

    cfg = WatchlistConfig()

    assert cfg.columns == ["last", "change_percent", "volume", "market_cap"]
    assert cfg.sort_column == "ticker"
    assert cfg.sort_direction == SortDirection.ASCENDING
    assert cfg.quotes == WatchlistConfig.DEFAULT_TICKERS
    assert cfg.query_frequency == WatchlistConfig.DEFAULT_QUERY_FREQUENCY


def test_columns_validation_and_duplicated() -> None:
    """Invalid and duplicate columns are dropped; ticker is implicit."""

    cfg = WatchlistConfig.model_validate(
        {
            "columns": [
                "ticker",  # ignored
                "last",
                "last",  # duplicate ignored
                "not_a_col",  # invalid ignored
                "volume",
            ]
        }
    )

    assert cfg.columns == ["last", "volume"]


def test_columns_empty_fallback_to_defaults() -> None:
    """Empty columns fall back to defaults."""

    cfg = WatchlistConfig.model_validate({"columns": []})
    assert cfg.columns == ["last", "change_percent", "volume", "market_cap"]


def test_columns_all_invalid_fallback_to_defaults() -> None:
    """All invalid columns fall back to defaults."""

    cfg = WatchlistConfig.model_validate({"columns": [" ", None]})
    assert cfg.columns == ["last", "change_percent", "volume", "market_cap"]


@pytest.mark.parametrize(
    ("sort_dir_input", "expected"),
    [
        pytest.param("asc", SortDirection.ASCENDING, id="asc-lower"),
        pytest.param("Asc", SortDirection.ASCENDING, id="asc-mixed"),
        pytest.param("ASC", SortDirection.ASCENDING, id="ASC-upper"),
        pytest.param("desc", SortDirection.DESCENDING, id="desc-lower"),
        pytest.param("Desc", SortDirection.DESCENDING, id="desc-mixed"),
        pytest.param("DESC", SortDirection.DESCENDING, id="DESC-upper"),
        pytest.param("x", SortDirection.ASCENDING, id="invalid-fallback"),
    ],
)
def test_sort_direction_parsing(sort_dir_input: str, expected: SortDirection) -> None:
    """Sort direction accepts strings and falls back to default on invalid."""

    cfg = WatchlistConfig.model_validate({"sort_direction": sort_dir_input})
    assert cfg.sort_direction == expected


def test_sort_column_membership() -> None:
    """Sort column not in columns falls back to first effective column (ticker)."""

    cfg = WatchlistConfig.model_validate(
        {
            "columns": ["last"],
            "sort_column": "not_present",
        }
    )
    assert cfg.sort_column == "ticker"


def test_quotes_normalization() -> None:
    """Quotes normalize to uppercase and deduplicate; empties ignored."""

    cfg = WatchlistConfig.model_validate(
        {"quotes": ["aapl", "", "AAPL", "vt", "BTC-usd"]}
    )
    assert cfg.quotes == ["AAPL", "VT", "BTC-USD"]


def test_quotes_empty_fallback_to_defaults() -> None:
    """Empty quotes list falls back to defaults."""

    cfg = WatchlistConfig.model_validate({"quotes": []})
    assert cfg.quotes == WatchlistConfig.DEFAULT_TICKERS


def test_quotes_all_invalid_fallback_to_defaults() -> None:
    """Empty quotes list falls back to defaults."""

    cfg = WatchlistConfig.model_validate({"quotes": [" ", "    "]})
    assert cfg.quotes == WatchlistConfig.DEFAULT_TICKERS


@pytest.mark.parametrize(("freq", "expected"), [(0, 60), (1, 60), (2, 2), (120, 120)])
def test_query_frequency_validation(freq: int, expected: int) -> None:
    """Query frequency <= 1 falls back to default; otherwise kept."""

    cfg = WatchlistConfig.model_validate({"query_frequency": freq})
    assert cfg.query_frequency == expected


_TEST_COLUMNS = ["last", "change_percent", "volume"]
_TEST_SORT_COLUMN = "last"
_TEST_SORT_DIRECTION = SortDirection.DESCENDING
_TEST_QUOTES = ["MSFT", "SPY"]
_TEST_QUERY_FREQUENCY = 30


def test_roundtrip_serialization() -> None:
    """Model dumps and validates back with equivalent values."""

    original = WatchlistConfig(
        columns=_TEST_COLUMNS,
        sort_column="last",
        sort_direction=SortDirection.DESCENDING,
        quotes=["msft", "spy"],
        query_frequency=30,
    )

    data = original.model_dump()
    restored = WatchlistConfig.model_validate(data)

    assert restored.columns == _TEST_COLUMNS
    assert restored.sort_column == _TEST_SORT_COLUMN
    assert restored.sort_direction == _TEST_SORT_DIRECTION
    assert restored.quotes == _TEST_QUOTES
    assert restored.query_frequency == _TEST_QUERY_FREQUENCY


def test_sort_direction_assignment_accepts_enum() -> None:
    """Assignment allows only valid sort direction values."""

    cfg = WatchlistConfig()

    cfg.sort_direction = SortDirection.DESCENDING

    assert cfg.sort_direction is SortDirection.DESCENDING


def test_sort_direction_assignment_rejects_invalid_value() -> None:
    """Assignment rejects invalid sort direction values."""

    cfg = WatchlistConfig()

    with pytest.raises(ValidationError):
        cfg.sort_direction = "sideways"  # pyright: ignore[reportAttributeAccessIssue]


def test_move_column_reorders_columns_and_updates() -> None:
    """Move column reorders the active list and refreshes columns."""

    config = DoubloonConfig()
    config.watchlist.columns = _TEST_COLUMNS.copy()

    app = _MoveColumnTestApp(config)
    with app._context():
        screen = _MoveColumnTestScreen()
        screen.move_column("change_percent", 0)

        assert config.watchlist.columns == ["change_percent", "last", "volume"]
        assert screen.update_calls == 1


def test_move_column_same_index_is_noop() -> None:
    """Move column skips updates when target index is unchanged."""

    config = DoubloonConfig()
    config.watchlist.columns = _TEST_COLUMNS.copy()

    app = _MoveColumnTestApp(config)
    with app._context():
        screen = _MoveColumnTestScreen()
        screen.move_column("change_percent", 1)

        assert config.watchlist.columns == _TEST_COLUMNS
        assert screen.update_calls == 0


def test_move_column_rejects_inactive_key() -> None:
    """Move column rejects keys that are not active."""

    config = DoubloonConfig()
    config.watchlist.columns = _TEST_COLUMNS.copy()

    app = _MoveColumnTestApp(config)
    with app._context():
        screen = _MoveColumnTestScreen()
        with pytest.raises(ValueError):  # noqa: PT011
            screen.move_column("missing", 0)

        assert config.watchlist.columns == _TEST_COLUMNS
        assert screen.update_calls == 0


@pytest.mark.parametrize("new_index", [-1, len(_TEST_COLUMNS)])
def test_move_column_rejects_invalid_index(new_index: int) -> None:
    """Move column rejects invalid destination indices."""

    config = DoubloonConfig()
    config.watchlist.columns = _TEST_COLUMNS.copy()

    app = _MoveColumnTestApp(config)
    with app._context():
        screen = _MoveColumnTestScreen()
        with pytest.raises(ValueError):  # noqa: PT011
            screen.move_column("last", new_index)

        assert config.watchlist.columns == _TEST_COLUMNS
        assert screen.update_calls == 0
