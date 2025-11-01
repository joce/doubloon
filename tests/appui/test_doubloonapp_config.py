"""Test behavior of DoubloonConfig model."""

from __future__ import annotations

import logging

import pytest
from pydantic import ValidationError

from appui._enums import LoggingLevel, TimeFormat
from appui.doubloon_config import DoubloonConfig
from appui.watchlist_config import WatchlistConfig


def test_default_values() -> None:
    """Test that default values are set correctly."""

    config = DoubloonConfig()

    assert config.title == "Doubloon"
    assert config.log_level == logging.INFO
    assert config.time_format == TimeFormat.TWENTY_FOUR_HOUR


def test_default_watchlist_is_watchlist_config() -> None:
    """Default config produces a watchlist model instance."""

    config = DoubloonConfig()

    assert isinstance(config.watchlist, WatchlistConfig)


def test_basic_assignment() -> None:
    """Test basic field assignment with valid values."""

    config = DoubloonConfig(
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
        pytest.param(LoggingLevel.NOTSET, logging.NOTSET, id="notset"),
        pytest.param(LoggingLevel.DEBUG, logging.DEBUG, id="debug"),
        pytest.param(LoggingLevel.INFO, logging.INFO, id="info"),
        pytest.param(LoggingLevel.WARNING, logging.WARNING, id="warning"),
        pytest.param(LoggingLevel.ERROR, logging.ERROR, id="error"),
        pytest.param(LoggingLevel.CRITICAL, logging.CRITICAL, id="critical"),
    ],
)
def test_log_level_validator_with_valid_values(
    input_level: LoggingLevel, expected_level: int
) -> None:
    """Test log level validator with valid integer values."""

    config = DoubloonConfig(log_level=input_level)
    assert config.log_level == expected_level


@pytest.mark.parametrize(
    ("input_string", "expected_level"),
    [
        pytest.param("NOTSET", logging.NOTSET, id="notset"),
        pytest.param("DEBUG", logging.DEBUG, id="debug"),
        pytest.param("INFO", logging.INFO, id="info"),
        pytest.param("WARNING", logging.WARNING, id="warning"),
        pytest.param("ERROR", logging.ERROR, id="error"),
        pytest.param("CRITICAL", logging.CRITICAL, id="critical"),
        pytest.param("INVALID", logging.ERROR, id="invalid-fallback"),
    ],
)
def test_log_level_validator_with_string_via_model_validate(
    input_string: str, expected_level: int
) -> None:
    """Test log level validator with string values via model_validate."""

    data = {"log_level": input_string}
    config = DoubloonConfig.model_validate(data)
    assert config.log_level == expected_level


@pytest.mark.parametrize(
    ("input_string", "expected_format"),
    [
        pytest.param("12h", TimeFormat.TWELVE_HOUR, id="12h-lower"),
        pytest.param("12H", TimeFormat.TWELVE_HOUR, id="12H-upper"),
        pytest.param("24h", TimeFormat.TWENTY_FOUR_HOUR, id="24h-lower"),
        pytest.param("24H", TimeFormat.TWENTY_FOUR_HOUR, id="24H-upper"),
        pytest.param("invalid", TimeFormat.TWENTY_FOUR_HOUR, id="invalid-fallback"),
    ],
)
def test_time_format_validator_with_string_via_model_validate(
    input_string: str, expected_format: TimeFormat
) -> None:
    """Test time format validator with string values via model_validate."""

    data = {"time_format": input_string}
    config = DoubloonConfig.model_validate(data)
    assert config.time_format == expected_format


def test_roundtrip_serialization() -> None:
    """Model dumps and validates back with equivalent values."""

    original = DoubloonConfig(
        title="Test Config",
        log_level=LoggingLevel.WARNING,
        time_format=TimeFormat.TWELVE_HOUR,
    )

    # Serialize
    data = original.model_dump()
    assert data["log_level"] == "warning"

    # Deserialize
    restored = DoubloonConfig.model_validate(data)

    assert restored.title == original.title
    assert restored.log_level == original.log_level
    assert restored.time_format == original.time_format


def test_model_dump_log_level_lowercase() -> None:
    """Model dump produces lowercase string log level."""

    config = DoubloonConfig(log_level=LoggingLevel.CRITICAL)

    dumped = config.model_dump()

    assert dumped["log_level"] == "critical"


def test_model_dump_log_level_numeric_fallback() -> None:
    """Model dump falls back to numeric string when level is unnamed."""

    config = DoubloonConfig()

    object.__setattr__(config, "log_level", 5)  # noqa: PLC2801 - bypasses frozen model

    dumped = config.model_dump()

    assert dumped["log_level"] == "5"


def test_watchlist_default_factory_produces_unique_instances() -> None:
    """Default factory yields distinct watchlist instances per config."""

    first = DoubloonConfig()
    second = DoubloonConfig()

    assert first.watchlist == second.watchlist
    assert first.watchlist is not second.watchlist


def test_watchlist_accepts_dict_payload() -> None:
    """Model coerce dict payloads into WatchlistConfig."""

    config = DoubloonConfig.model_validate({"watchlist": {"quotes": ["SPY"]}})

    assert isinstance(config.watchlist, WatchlistConfig)


def test_log_level_assignment_accepts_enum() -> None:
    """Assignment allows only valid logging levels."""

    config = DoubloonConfig()

    config.log_level = LoggingLevel.WARNING

    assert config.log_level == logging.WARNING


def test_log_level_assignment_rejects_invalid_value() -> None:
    """Assignment rejects invalid logging level values."""

    config = DoubloonConfig()

    with pytest.raises(ValidationError):
        config.log_level = "verbose"  # pyright: ignore[reportAttributeAccessIssue]


def test_time_format_assignment_accepts_enum() -> None:
    """Assignment allows only valid time format values."""

    config = DoubloonConfig()

    config.time_format = TimeFormat.TWELVE_HOUR

    assert config.time_format is TimeFormat.TWELVE_HOUR


def test_time_format_assignment_rejects_invalid_value() -> None:
    """Assignment rejects invalid time format values."""

    config = DoubloonConfig()

    with pytest.raises(ValidationError):
        config.time_format = "13h"  # pyright: ignore[reportAttributeAccessIssue]
