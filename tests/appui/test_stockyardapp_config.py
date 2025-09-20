"""Test behavior of StockyardConfig model."""

from __future__ import annotations

import logging

import pytest

from appui._enums import LoggingLevel, TimeFormat
from appui.stockyard_config import StockyardConfig
from appui.watchlist_config import WatchlistConfig


def test_default_values() -> None:
    """Test that default values are set correctly."""
    config = StockyardConfig()

    assert config.title == "Stockyard"
    assert config.log_level == logging.INFO
    assert config.time_format == TimeFormat.TWENTY_FOUR_HOUR


def test_default_watchlist_is_watchlist_config() -> None:
    """Default config produces a watchlist model instance."""
    config = StockyardConfig()

    assert isinstance(config.watchlist, WatchlistConfig)


def test_basic_assignment() -> None:
    """Test basic field assignment with valid values."""
    config = StockyardConfig(
        title="Custom Title",
        log_level=LoggingLevel.DEBUG,
        time_format=TimeFormat.TWELVE_HOUR,
    )

    assert config.title == "Custom Title"
    assert config.log_level == logging.DEBUG
    assert config.time_format == TimeFormat.TWELVE_HOUR


@pytest.mark.parametrize(
    ("input_level", "expected_level"),
    [
        (LoggingLevel.NOTSET, logging.NOTSET),
        (LoggingLevel.DEBUG, logging.DEBUG),
        (LoggingLevel.INFO, logging.INFO),
        (LoggingLevel.WARNING, logging.WARNING),
        (LoggingLevel.ERROR, logging.ERROR),
        (LoggingLevel.CRITICAL, logging.CRITICAL),
    ],
)
def test_log_level_validator_with_valid_values(
    input_level: LoggingLevel, expected_level: int
) -> None:
    """Test log level validator with valid integer values."""
    config = StockyardConfig(log_level=input_level)
    assert config.log_level == expected_level


@pytest.mark.parametrize(
    ("input_string", "expected_level"),
    [
        ("NOTSET", logging.NOTSET),
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
        ("INVALID", logging.ERROR),
    ],
)
def test_log_level_validator_with_string_via_model_validate(
    input_string: str, expected_level: int
) -> None:
    """Test log level validator with string values via model_validate."""
    data = {"log_level": input_string}
    config = StockyardConfig.model_validate(data)
    assert config.log_level == expected_level


@pytest.mark.parametrize(
    ("input_string", "expected_format"),
    [
        ("12h", TimeFormat.TWELVE_HOUR),
        ("12H", TimeFormat.TWELVE_HOUR),
        ("24h", TimeFormat.TWENTY_FOUR_HOUR),
        ("24H", TimeFormat.TWENTY_FOUR_HOUR),
        ("invalid", TimeFormat.TWENTY_FOUR_HOUR),
    ],
)
def test_time_format_validator_with_string_via_model_validate(
    input_string: str, expected_format: TimeFormat
) -> None:
    """Test time format validator with string values via model_validate."""
    data = {"time_format": input_string}
    config = StockyardConfig.model_validate(data)
    assert config.time_format == expected_format


def test_roundtrip_serialization() -> None:
    """Model dumps and validates back with equivalent values."""
    original = StockyardConfig(
        title="Test Config",
        log_level=LoggingLevel.WARNING,
        time_format=TimeFormat.TWELVE_HOUR,
    )

    # Serialize
    data = original.model_dump()
    assert data["log_level"] == "warning"

    # Deserialize
    restored = StockyardConfig.model_validate(data)

    assert restored.title == original.title
    assert restored.log_level == original.log_level
    assert restored.time_format == original.time_format


def test_model_dump_log_level_lowercase() -> None:
    """Model dump produces lowercase string log level."""
    config = StockyardConfig(log_level=LoggingLevel.CRITICAL)

    dumped = config.model_dump()

    assert dumped["log_level"] == "critical"


def test_watchlist_default_factory_produces_unique_instances() -> None:
    """Default factory yields distinct watchlist instances per config."""
    first = StockyardConfig()
    second = StockyardConfig()

    assert first.watchlist == second.watchlist
    assert first.watchlist is not second.watchlist


def test_watchlist_accepts_dict_payload() -> None:
    """Model coerce dict payloads into WatchlistConfig."""
    config = StockyardConfig.model_validate({"watchlist": {"quotes": ["SPY"]}})

    assert isinstance(config.watchlist, WatchlistConfig)


def test_log_level_assignment_accepts_enum() -> None:
    """Assignment allows only valid logging levels."""
    config = StockyardConfig()

    config.log_level = LoggingLevel.WARNING

    assert config.log_level == logging.WARNING
