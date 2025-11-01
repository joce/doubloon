"""The configuration of the watchlist screen."""

from __future__ import annotations

import logging
import sys
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ._enums import SortDirection, coerce_enum_member
from ._lenient_assignment_mixin import LenientAssignmentMixin
from ._quote_column_definitions import ALL_QUOTE_COLUMNS, TICKER_COLUMN_KEY

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

_LOGGER = logging.getLogger(__name__)


class WatchlistConfig(LenientAssignmentMixin, BaseModel):
    """The Watchlist screen configuration.

    Notes:
        - The `columns` field contains only non-`ticker` columns. The table always
          includes the `ticker` column as the first column via `table_columns`.
        - Validation mirrors the previous manual implementation, with warnings
          logged for invalid or duplicate values.
    """

    model_config = ConfigDict(validate_assignment=True)

    # Constants (not part of the model schema)
    DEFAULT_COLUMN_NAMES: ClassVar[list[str]] = [
        "last",
        "change_percent",
        "volume",
        "market_cap",
    ]
    DEFAULT_TICKERS: ClassVar[list[str]] = [
        "AAPL",
        "F",
        "VT",
        "^DJI",
        "ARKK",
        "GC=F",
        "EURUSD=X",
        "BTC-USD",
    ]
    DEFAULT_SORT_DIRECTION: ClassVar[SortDirection] = SortDirection.ASCENDING
    DEFAULT_QUERY_FREQUENCY: ClassVar[int] = 60

    # Pydantic model fields
    columns: list[str] = Field(
        default_factory=lambda: WatchlistConfig.DEFAULT_COLUMN_NAMES[:],
        description="Non-ticker columns to display (ticker is always first)",
    )
    sort_column: str = Field(
        default=TICKER_COLUMN_KEY,
        description="Key of the column to sort by (includes 'ticker')",
    )
    sort_direction: SortDirection = Field(
        default=DEFAULT_SORT_DIRECTION, description="Sort direction"
    )
    quotes: list[str] = Field(
        default_factory=lambda: WatchlistConfig.DEFAULT_TICKERS[:],
        description="List of quote symbols",
    )
    query_frequency: int = Field(
        default=DEFAULT_QUERY_FREQUENCY,
        description="Refresh/query frequency in seconds",
        ge=1,
    )

    # -------------------- Validators --------------------
    @field_validator("columns", mode="before")
    @classmethod
    def _normalize_columns(cls, v: list[str] | None) -> list[str]:
        """Normalize and validate the list of non-ticker columns.

        Args:
            v (list[str] | None): The provided columns list, excluding `ticker`.

        Returns:
            list[str]: A filtered, de-duplicated list of valid column keys.
        """

        if not v:
            _LOGGER.warning("No columns specified in config; using defaults")
            return cls.DEFAULT_COLUMN_NAMES[:]

        filtered: list[str] = []
        seen: set[str] = set()
        for col in v:
            if col == TICKER_COLUMN_KEY:
                # Always implicit; ignore if provided.
                continue
            if col not in ALL_QUOTE_COLUMNS:
                _LOGGER.warning("Invalid column key '%s' specified in config", col)
                continue
            if col in seen:
                _LOGGER.warning("Duplicate column key '%s' specified in config", col)
                continue
            seen.add(col)
            filtered.append(col)

        if not filtered:
            _LOGGER.warning("All provided columns were invalid; using defaults")
            return cls.DEFAULT_COLUMN_NAMES[:]

        return filtered

    @field_validator("sort_direction", mode="before")
    @classmethod
    def _validate_sort_direction(cls, v: SortDirection | str | None) -> SortDirection:
        """Validate sort direction, accepting enum or string values.

        Args:
            v (SortDirection | str | None): The provided sort direction value or string.

        Returns:
            SortDirection: A valid sort direction.
        """

        direction = coerce_enum_member(
            SortDirection, v, strict=not cls._fallback_enabled()
        )
        if direction is not None:
            return direction
        return cls.DEFAULT_SORT_DIRECTION

    @field_validator("quotes", mode="before")
    @classmethod
    def _normalize_quotes(cls, v: list[str] | None) -> list[str]:
        """Normalize quotes: uppercase, remove empties and duplicates.

        Args:
            v (list[str] | None): The provided list of quote symbols.

        Returns:
            list[str]: A cleaned list of symbols or defaults if empty.
        """

        if not v:
            _LOGGER.warning("No quotes specified in config; using defaults")
            return cls.DEFAULT_TICKERS[:]

        result: list[str] = []
        seen: set[str] = set()
        for symbol in [s.strip() for s in v]:
            if not symbol:
                _LOGGER.warning("Empty quote symbol specified in config")
                continue
            up = symbol.upper()
            if up in seen:
                _LOGGER.warning("Duplicate quote symbol %s specified in config", up)
                continue
            seen.add(up)
            result.append(up)

        if not result:
            _LOGGER.warning("All provided quotes were invalid; using defaults")
            return cls.DEFAULT_TICKERS[:]
        return result

    @field_validator("query_frequency", mode="before")
    @classmethod
    def _validate_query_frequency(cls, v: int | None) -> int:
        """Validate query frequency; fallback to default when invalid.

        Args:
            v (int | None): The provided frequency in seconds.

        Returns:
            int: A valid frequency (>= 1), or the default if invalid.
        """

        if v is None or v <= 1:
            _LOGGER.warning(
                "Invalid query frequency specified in config; using default"
            )
            return cls.DEFAULT_QUERY_FREQUENCY
        return v

    @model_validator(mode="after")
    def _finalize_validation(self) -> Self:
        """Finalize cross-field validation for sort column membership.

        Ensures `sort_column` is one of `table_columns`; otherwise defaults to the
        first entry (which is always `ticker`).

        Returns:
            Self: The validated configuration instance.
        """

        if self.sort_column not in self.columns:
            object.__setattr__(  # noqa: PLC2801 - bypasses frozen model
                self, "sort_column", TICKER_COLUMN_KEY
            )
        return self
