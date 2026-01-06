"""Definitions of the available columns for the quote table."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from .enhanced_data_table import EnhancedTableCell
from .enums import Justify
from .formatting import (
    as_bool,
    as_compact,
    as_date,
    as_datetime,
    as_enum,
    as_float,
    as_percent,
)
from .quote_table import quote_column

if TYPE_CHECKING:
    from datetime import date, datetime
    from enum import Enum

    from .quote_table import QuoteColumn


TICKER_COLUMN_KEY: Final[str] = "ticker"

# TODO: Make these configurable
_GAINING_COLOR: Final[str] = "#00DD00"
_LOSING_COLOR: Final[str] = "#DD0000"


def _with_secondary_key(
    sort_value: float, secondary_key: str | None
) -> tuple[object, ...]:
    """Build a tuple suitable for use as a comparison key.

    Args:
        sort_value (float): The primary value to use for sorting.
        secondary_key (str | None): An optional secondary string key to use for
            tie-breaking.

    Returns:
        tuple[object, ...]: A tuple containing the primary sort value and, if
        provided, the secondary key.

    """

    return (sort_value, secondary_key) if secondary_key else (sort_value,)


class TextCell(EnhancedTableCell):
    """Cell that renders plain text with optional case-insensitive sorting."""

    def __init__(
        self,
        value: str,
        *,
        justification: Justify = Justify.LEFT,
        style: str = "",
        case_sensitive: bool = False,
        secondary_key: str | None = None,
    ) -> None:
        """Initialize the text cell.

        Args:
            value (str): The text value to display.
            justification (Justify): The text justification.
            style (str): The style string for the cell.
            case_sensitive (bool): Whether sorting should be case-sensitive.
            secondary_key (str | None): An optional secondary string key to use for
                tie-breaking during sorting.
        """

        primary = value if case_sensitive else value.lower()
        if secondary_key:
            sort_key = (
                primary,
                secondary_key if case_sensitive else secondary_key.lower(),
            )
        else:
            sort_key = (primary,)
        super().__init__(sort_key, value, justification, style)


class TickerCell(TextCell):
    """Cell specialized for ticker symbols."""

    def __init__(self, symbol: str, *, justification: Justify = Justify.LEFT) -> None:
        """Initialize the ticker cell.

        Args:
            symbol (str): The ticker symbol.
            justification (Justify): The text justification.
        """

        normalized = symbol or ""
        super().__init__(
            normalized.upper(),
            justification=justification,
            case_sensitive=False,
        )


class FloatCell(EnhancedTableCell):
    """Cell that renders float values with fixed precision."""

    def __init__(
        self,
        value: float | None,
        *,
        precision: int | None = None,
        justification: Justify = Justify.RIGHT,
        style: str = "",
        secondary_key: str | None = None,
    ) -> None:
        """Initialize the float cell.

        Args:
            value (float | None): The float value to display.
            precision (int | None): The number of decimal places to display.
            justification (Justify): The text justification.
            style (str): The style string for the cell.
            secondary_key (str | None): An optional secondary string key to use for
                tie-breaking during sorting.
        """

        safe_value = float("-inf") if value is None else value
        super().__init__(
            _with_secondary_key(safe_value, secondary_key),
            as_float(value, precision or 2),
            justification,
            style,
        )


class PercentCell(EnhancedTableCell):
    """Cell that renders percentage values."""

    def __init__(
        self,
        value: float | None,
        *,
        justification: Justify = Justify.RIGHT,
        style: str = "",
        secondary_key: str | None = None,
    ) -> None:
        """Initialize the percent cell.

        Args:
            value (float | None): The percentage value to display.
            justification (Justify): The text justification.
            style (str): The style string for the cell.
            secondary_key (str | None): An optional secondary string key to use for
                tie-breaking during sorting.
        """

        safe_value = float("-inf") if value is None else float(value)
        super().__init__(
            _with_secondary_key(safe_value, secondary_key),
            as_percent(value),
            justification,
            style,
        )


class CompactNumberCell(EnhancedTableCell):
    """Cell that renders large integers in a compact form."""

    def __init__(
        self,
        value: int | None,
        *,
        justification: Justify = Justify.RIGHT,
        style: str = "",
        secondary_key: str | None = None,
    ) -> None:
        """Initialize the compact number cell.

        Args:
            value (int | None): The integer value to display.
            justification (Justify): The text justification.
            style (str): The style string for the cell.
            secondary_key (str | None): An optional secondary string key to use for
                tie-breaking during sorting.
        """

        safe_value = float("-inf") if value is None else int(value)
        super().__init__(
            _with_secondary_key(safe_value, secondary_key),
            as_compact(value),
            justification,
            style,
        )


class DateCell(EnhancedTableCell):
    """Cell that renders date values."""

    def __init__(
        self,
        value: date | None,
        *,
        date_format: str | None = None,
        justification: Justify = Justify.LEFT,
        style: str = "",
        secondary_key: str | None = None,
    ) -> None:
        """Initialize the date cell.

        Args:
            value (date | None): The date value to display.
            date_format (str | None): Optional format override for display.
            justification (Justify): The text justification.
            style (str): The style string for the cell.
            secondary_key (str | None): An optional secondary string key to use for
                tie-breaking during sorting.
        """

        safe_value = float("-inf") if value is None else value.toordinal()
        super().__init__(
            _with_secondary_key(safe_value, secondary_key),
            as_date(value, date_format),
            justification,
            style,
        )


class DateTimeCell(EnhancedTableCell):
    """Cell that renders datetime values."""

    def __init__(
        self,
        value: datetime | None,
        *,
        datetime_format: str | None = None,
        justification: Justify = Justify.LEFT,
        style: str = "",
        secondary_key: str | None = None,
    ) -> None:
        """Initialize the datetime cell.

        Args:
            value (datetime | None): The datetime value to display.
            datetime_format (str | None): Optional format override for display.
            justification (Justify): The text justification.
            style (str): The style string for the cell.
            secondary_key (str | None): An optional secondary string key to use for
                tie-breaking during sorting.
        """

        safe_value = float("-inf") if value is None else value.timestamp()
        super().__init__(
            _with_secondary_key(safe_value, secondary_key),
            as_datetime(value, datetime_format),
            justification,
            style,
        )


class EnumCell(EnhancedTableCell):
    """Cell that renders enum values in title case."""

    def __init__(
        self,
        value: Enum | None,
        *,
        justification: Justify = Justify.LEFT,
        style: str = "",
        secondary_key: str | None = None,
    ) -> None:
        """Initialize the enum cell.

        Args:
            value (Enum | None): The enum value to display.
            justification (Justify): The text justification.
            style (str): The style string for the cell.
            secondary_key (str | None): An optional secondary string key to use for
                tie-breaking during sorting.
        """

        display_value = as_enum(value)
        primary = display_value.lower() if value is not None else ""
        sort_key = (primary, secondary_key.lower()) if secondary_key else (primary,)
        super().__init__(sort_key, display_value, justification, style)


class BooleanCell(EnhancedTableCell):
    """Cell that renders boolean values as checkboxes."""

    def __init__(
        self,
        *,
        value: bool | None,
        justification: Justify = Justify.CENTER,
        style: str = "",
        secondary_key: str | None = None,
    ) -> None:
        """Initialize the boolean cell.

        Args:
            value (bool | None): The boolean value to display.
            justification (Justify): The text justification.
            style (str): The style string for the cell.
            secondary_key (str | None): An optional secondary string key to use for
                tie-breaking during sorting.
        """

        safe_value = float("-inf") if value is None else float(value)
        super().__init__(
            _with_secondary_key(safe_value, secondary_key),
            as_bool(value=value),
            justification,
            style,
        )


def _get_style_for_value(value: float) -> str:
    """Get the style string based on the sign of a value.

    Args:
        value (float): The value for which to provide a style for.

    Returns:
        str: The style string corresponding to the sign.
            - Returns _GAINING_COLOR if sign is > 0.
            - Returns _LOSING_COLOR if sign is < 0.
            - Returns an empty string if sign is 0.
    """

    return _GAINING_COLOR if value > 0 else _LOSING_COLOR if value < 0 else ""


ALL_QUOTE_COLUMNS: Final[dict[str, QuoteColumn]] = {
    "ticker": (
        quote_column(
            "Ticker",
            full_name="Ticker Symbol",
            width=8,
            key="ticker",
            justification=Justify.LEFT,
            cell_factory=lambda q: TickerCell(
                q.symbol or "", justification=Justify.LEFT
            ),
        )
    ),
    "last": (
        quote_column(
            "Last",
            full_name="Market Price",
            width=10,
            key="last",
            cell_factory=lambda q: FloatCell(
                q.regular_market_price,
                precision=q.price_hint,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "change": (
        quote_column(
            "Change",
            full_name="Market Change",
            width=10,
            key="change",
            cell_factory=lambda q: FloatCell(
                q.regular_market_change,
                precision=q.price_hint,
                justification=Justify.RIGHT,
                style=_get_style_for_value(q.regular_market_change),
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "change_percent": (
        quote_column(
            "Chg %",
            full_name="Market Change Percent",
            width=8,
            key="change_percent",
            cell_factory=lambda q: PercentCell(
                q.regular_market_change_percent,
                justification=Justify.RIGHT,
                style=_get_style_for_value(q.regular_market_change_percent),
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "open": (
        quote_column(
            "Open",
            full_name="Market Open",
            width=10,
            key="open",
            cell_factory=lambda q: FloatCell(
                q.regular_market_open,
                precision=q.price_hint,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "low": (
        quote_column(
            "Low",
            full_name="Day Low",
            width=10,
            key="low",
            cell_factory=lambda q: FloatCell(
                q.regular_market_day_low,
                precision=q.price_hint,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "high": (
        quote_column(
            "High",
            full_name="Day High",
            width=10,
            key="high",
            cell_factory=lambda q: FloatCell(
                q.regular_market_day_high,
                precision=q.price_hint,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "_52w_low": (
        quote_column(
            "52w Low",
            full_name="52-Week Low",
            width=10,
            key="_52w_low",
            cell_factory=lambda q: FloatCell(
                q.fifty_two_week_low,
                precision=q.price_hint,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "_52w_high": (
        quote_column(
            "52w High",
            full_name="52-Week High",
            width=10,
            key="_52w_high",
            cell_factory=lambda q: FloatCell(
                q.fifty_two_week_high,
                precision=q.price_hint,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "volume": (
        quote_column(
            "Volume",
            full_name="Market Volume",
            width=10,
            key="volume",
            cell_factory=lambda q: CompactNumberCell(
                q.regular_market_volume,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "avg_volume": (
        quote_column(
            "Avg Vol",
            full_name="Average Daily Volume (3 Month)",
            width=10,
            key="avg_volume",
            cell_factory=lambda q: CompactNumberCell(
                q.average_daily_volume_3_month,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "pe": (
        quote_column(
            "P/E",
            full_name="Trailing Price-to-Earnings Ratio",
            width=6,
            key="pe",
            cell_factory=lambda q: FloatCell(
                q.trailing_pe,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "dividend": (
        quote_column(
            "Div",
            full_name="Dividend Yield",
            width=6,
            key="dividend",
            cell_factory=lambda q: FloatCell(
                q.dividend_yield,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "market_cap": (
        quote_column(
            "Mkt Cap",
            full_name="Market Capitalization",
            width=10,
            key="market_cap",
            cell_factory=lambda q: CompactNumberCell(
                q.market_cap,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "dividend_date": (
        quote_column(
            "Div Date",
            full_name="Dividend Date",
            width=10,
            key="dividend_date",
            justification=Justify.LEFT,
            cell_factory=lambda q: DateCell(
                q.dividend_date,
                justification=Justify.LEFT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "market_state": (
        quote_column(
            "Mkt State",
            full_name="Market State",
            width=10,
            key="market_state",
            justification=Justify.LEFT,
            cell_factory=lambda q: EnumCell(
                q.market_state,
                justification=Justify.LEFT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "option_type": (
        quote_column(
            "Opt Type",
            full_name="Option Type",
            width=8,
            key="option_type",
            justification=Justify.LEFT,
            cell_factory=lambda q: EnumCell(
                q.option_type,
                justification=Justify.LEFT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "quote_type": (
        quote_column(
            "Type",
            full_name="Quote Type",
            width=15,
            key="quote_type",
            justification=Justify.LEFT,
            cell_factory=lambda q: EnumCell(
                q.quote_type,
                justification=Justify.LEFT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "tradeable": (
        quote_column(
            "Tradeable",
            full_name="Tradeable",
            width=9,
            key="tradeable",
            justification=Justify.CENTER,
            cell_factory=lambda q: BooleanCell(
                value=q.tradeable,
                justification=Justify.CENTER,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "post_market_datetime": (
        quote_column(
            "Post Mkt",
            full_name="Post-Market Datetime",
            width=16,
            key="post_market_datetime",
            justification=Justify.LEFT,
            cell_factory=lambda q: DateTimeCell(
                q.post_market_datetime,
                justification=Justify.LEFT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
}
"""
A dictionary that contains QuoteColumns available for the quote table.

Each QuoteColumn is keyed by its key name.
"""
