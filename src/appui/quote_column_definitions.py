"""Definitions of the available columns for the quote table."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from .enhanced_data_table import EnhancedTableCell
from .enums import Justify
from .formatting import as_compact, as_float, as_percent
from .quote_table import quote_column

if TYPE_CHECKING:
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
        safe_value = float("-inf") if value is None else int(value)
        super().__init__(
            _with_secondary_key(safe_value, secondary_key),
            as_compact(value),
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
    "52w_low": (
        quote_column(
            "52w Low",
            width=10,
            key="52w_low",
            cell_factory=lambda q: FloatCell(
                q.fifty_two_week_low,
                precision=q.price_hint,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
    "52w_high": (
        quote_column(
            "52w High",
            width=10,
            key="52w_high",
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
            width=10,
            key="market_cap",
            cell_factory=lambda q: CompactNumberCell(
                q.market_cap,
                justification=Justify.RIGHT,
                secondary_key=q.symbol or "",
            ),
        )
    ),
}
"""
A dictionary that contains QuoteColumns available for the quote table.

Each QuoteColumn is keyed by its key name.
"""
