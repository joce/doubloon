"""The configuration of the whole doubloon application."""

from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from .enums import LoggingLevel, TimeFormat, coerce_enum_member
from .lenient_assignment_mixin import LenientAssignmentMixin
from .watchlist_config import WatchlistConfig


class DoubloonConfig(LenientAssignmentMixin, BaseModel):
    """The Doubloon app configuration."""

    model_config = ConfigDict(validate_assignment=True)

    # Pydantic model fields
    title: str = Field(default="Doubloon", description="The title of the app")
    log_level: LoggingLevel = Field(
        default=LoggingLevel.INFO, description="The logging level"
    )
    time_format: TimeFormat = Field(
        default=TimeFormat.TWENTY_FOUR_HOUR, description="The time format"
    )
    watchlist: WatchlistConfig = Field(
        default_factory=WatchlistConfig,
        description="Watchlist screen configuration",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def _validate_log_level(cls, v: LoggingLevel | int | str | None) -> LoggingLevel:
        """Validate the log level.

        Args:
            v: The log level value to validate.

        Returns:
            LoggingLevel: A valid logging level.
        """

        level = coerce_enum_member(LoggingLevel, v, strict=not cls._fallback_enabled())
        if level is not None:
            return level
        return LoggingLevel.ERROR

    @field_serializer("log_level")
    @classmethod
    def _serialize_log_level(cls, v: LoggingLevel) -> str:
        """Serialize the log level as a lowercase string.

        Args:
            v: The log level value to serialize.

        Returns:
            str: The lowercase log level name if known, otherwise the numeric string.
        """

        level_name: str = logging.getLevelName(int(v))
        if not level_name.startswith("Level "):
            return level_name.lower()
        return str(int(v))

    @field_validator("time_format", mode="before")
    @classmethod
    def _validate_time_format(cls, v: TimeFormat | str | None) -> TimeFormat:
        """Validate the time format.

        Args:
            v: The time format value to validate.

        Returns:
            TimeFormat: A valid time format.
        """

        fmt = coerce_enum_member(TimeFormat, v, strict=not cls._fallback_enabled())
        if fmt is not None:
            return fmt
        return TimeFormat.TWENTY_FOUR_HOUR
