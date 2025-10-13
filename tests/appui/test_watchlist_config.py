"""Tests for WatchlistConfig model behavior."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from appui._enums import SortDirection
from appui.watchlist_config import WatchlistConfig

# pylint: disable=protected-access
# pyright: reportPrivateUsage=none


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


@pytest.mark.parametrize(
    ("sort_dir_input", "expected"),
    [
        ("asc", SortDirection.ASCENDING),
        ("ASC", SortDirection.ASCENDING),
        ("desc", SortDirection.DESCENDING),
        ("DESC", SortDirection.DESCENDING),
        ("x", SortDirection.ASCENDING),
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
