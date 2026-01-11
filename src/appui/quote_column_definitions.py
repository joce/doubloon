"""Definitions of the available columns for the quote table."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from types import UnionType
from typing import TYPE_CHECKING, Any, Final, Union, cast, get_args, get_origin

from calahan.yquote import YQuote

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
    from collections.abc import Callable
    from typing import ClassVar

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

    default_justification: ClassVar[Justify] = Justify.LEFT

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
        secondary = (
            (secondary_key if case_sensitive else secondary_key.lower())
            if secondary_key
            else None
        )
        sort_key = (primary, secondary) if secondary else (primary,)
        super().__init__(sort_key, value, justification, style)


class TickerCell(TextCell):
    """Cell specialized for ticker symbols."""

    default_justification: ClassVar[Justify] = Justify.LEFT

    def __init__(
        self,
        symbol: str,
        *,
        justification: Justify = Justify.LEFT,
        style: str = "",
        secondary_key: str | None = None,
    ) -> None:
        """Initialize the ticker cell.

        Args:
            symbol (str): The ticker symbol.
            justification (Justify): The text justification.
            style (str): Style string (unused, for API uniformity).
            secondary_key (str | None): Secondary sort key (unused, for API uniformity).
        """

        del style, secondary_key  # Unused; ticker sorts by symbol only
        normalized = symbol or ""
        super().__init__(
            normalized.upper(),
            justification=justification,
            case_sensitive=False,
        )


class FloatCell(EnhancedTableCell):
    """Cell that renders float values with fixed precision."""

    default_justification: ClassVar[Justify] = Justify.RIGHT

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

    default_justification: ClassVar[Justify] = Justify.RIGHT

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

    default_justification: ClassVar[Justify] = Justify.RIGHT

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

    default_justification: ClassVar[Justify] = Justify.LEFT

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

    default_justification: ClassVar[Justify] = Justify.LEFT

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

    default_justification: ClassVar[Justify] = Justify.LEFT

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

    default_justification: ClassVar[Justify] = Justify.CENTER

    def __init__(
        self,
        value: bool | None,  # noqa: FBT001
        *,
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


@dataclass(frozen=True)
class ColumnSpec:
    """Minimal specification for a quote column."""

    key: str
    short_name: str
    full_name: str
    width: int
    attr_name: str | None = None
    precision: int | None = None
    justification: Justify | None = None
    style_fn: Callable[[Any], str] | None = None
    cell_class: type[EnhancedTableCell] | None = None


def _get_field_type(field_annotation: object) -> type:
    """Extract the actual type from a field annotation.

    Unwrap Optional/Union annotations and return the origin for parameterized types.

    Args:
        field_annotation (object): The type annotation from a Pydantic field.

    Returns:
        type: The underlying non-None type for Optional/Union annotations, otherwise
            the origin or original annotation.
    """

    origin = get_origin(field_annotation)
    if origin is None:
        return cast("type", field_annotation)

    args = get_args(field_annotation)
    if origin in {Union, UnionType} and args:
        # Filter out NoneType and return the first non-None type.
        non_none_types = [t for t in args if t is not type(None)]
        if non_none_types:
            return cast("type", non_none_types[0])

    return cast("type", origin)


_TYPE_TO_CELL: Final[dict[type, type[EnhancedTableCell]]] = {
    str: TextCell,
    float: FloatCell,
    int: CompactNumberCell,
    bool: BooleanCell,
    date: DateCell,
    datetime: DateTimeCell,
}


def _get_field_type_for_attr(attr_name: str) -> type:
    """Get the field type for a YQuote attribute.

    Args:
        attr_name (str): The attribute name to look up.

    Returns:
        type: The field type.

    Raises:
        ValueError: If the attribute is not found in YQuote model.
    """

    field_info = YQuote.model_fields.get(attr_name)
    if field_info is not None:
        return _get_field_type(field_info.annotation)

    computed_field = YQuote.model_computed_fields.get(attr_name)
    if computed_field is not None:
        return _get_field_type(computed_field.return_type)

    msg = f"Field {attr_name} not found in YQuote model"
    raise ValueError(msg)


def _cell_class_for_type(field_type: type) -> type[EnhancedTableCell]:
    """Get the appropriate cell class for a field type.

    Args:
        field_type (type): The field type.

    Returns:
        type[EnhancedTableCell]: The cell class to use.
    """

    cell_class = _TYPE_TO_CELL.get(field_type)
    if cell_class is not None:
        return cell_class

    # Check if it's an Enum subclass
    try:
        if issubclass(field_type, Enum):
            return EnumCell
    except TypeError:
        pass

    return TextCell


def _build_column(spec: ColumnSpec) -> QuoteColumn:
    """Generate a QuoteColumn from a spec using type introspection.

    Args:
        spec (ColumnSpec): The column specification.

    Returns:
        QuoteColumn: A fully configured quote column.
    """

    attr_name = spec.attr_name or spec.key
    field_type = _get_field_type_for_attr(attr_name)

    cell_class = spec.cell_class or _cell_class_for_type(field_type)
    justify = spec.justification or cell_class.default_justification

    def cell_factory(q: YQuote) -> EnhancedTableCell:
        value = getattr(q, attr_name)
        style = spec.style_fn(value) if spec.style_fn and value is not None else ""
        kwargs: dict[str, Any] = {
            "justification": justify,
            "secondary_key": q.symbol or "",
            "style": style,
        }
        if cell_class is FloatCell:
            kwargs["precision"] = spec.precision or q.price_hint

        return cell_class(value, **kwargs)

    return quote_column(
        spec.short_name,
        full_name=spec.full_name,
        width=spec.width,
        key=spec.key,
        justification=justify,
        cell_factory=cell_factory,
    )


COLUMN_SPECS: Final[list[ColumnSpec]] = [
    # === Identity & Basic Info ===
    ColumnSpec(
        "ticker",
        "Ticker",
        "Ticker Symbol",
        8,
        attr_name="symbol",
        cell_class=TickerCell,
    ),
    ColumnSpec("short_name", "Name", "Short Name", 20),
    ColumnSpec("long_name", "Long Name", "Long Name", 30),
    ColumnSpec("display_name", "Display", "Display Name", 20),
    ColumnSpec("quote_type", "Type", "Quote Type", 15),
    ColumnSpec("currency", "Ccy", "Currency", 5),
    ColumnSpec("financial_currency", "Fin Ccy", "Financial Currency", 7),
    # === Price Data ===
    ColumnSpec(
        "last",
        "Last",
        "Market Price",
        10,
        attr_name="regular_market_price",
    ),
    ColumnSpec(
        "change",
        "Change",
        "Market Change",
        10,
        attr_name="regular_market_change",
        style_fn=_get_style_for_value,
    ),
    ColumnSpec(
        "change_percent",
        "Chg %",
        "Market Change Percent",
        8,
        attr_name="regular_market_change_percent",
        cell_class=PercentCell,
        style_fn=_get_style_for_value,
    ),
    ColumnSpec("open", "Open", "Market Open", 10, attr_name="regular_market_open"),
    ColumnSpec("low", "Low", "Day Low", 10, attr_name="regular_market_day_low"),
    ColumnSpec("high", "High", "Day High", 10, attr_name="regular_market_day_high"),
    ColumnSpec(
        "day_range",
        "Day Range",
        "Day Range",
        20,
        attr_name="regular_market_day_range",
    ),
    ColumnSpec(
        "prev_close",
        "Prev Close",
        "Previous Close",
        10,
        attr_name="regular_market_previous_close",
    ),
    # === 52-Week Data ===
    ColumnSpec(
        "_52w_low",
        "52w Low",
        "52-Week Low",
        10,
        attr_name="fifty_two_week_low",
    ),
    ColumnSpec(
        "_52w_high",
        "52w High",
        "52-Week High",
        10,
        attr_name="fifty_two_week_high",
    ),
    ColumnSpec(
        "_52w_low_change",
        "52wL Chg",
        "52-Week Low Change",
        10,
        attr_name="fifty_two_week_low_change",
        style_fn=_get_style_for_value,
    ),
    ColumnSpec(
        "_52w_high_change",
        "52wH Chg",
        "52-Week High Change",
        10,
        attr_name="fifty_two_week_high_change",
        style_fn=_get_style_for_value,
    ),
    ColumnSpec(
        "_52w_low_change_percent",
        "52wL %",
        "52-Week Low Change Percent",
        8,
        attr_name="fifty_two_week_low_change_percent",
        cell_class=PercentCell,
        style_fn=_get_style_for_value,
    ),
    ColumnSpec(
        "_52w_high_change_percent",
        "52wH %",
        "52-Week High Change Percent",
        8,
        attr_name="fifty_two_week_high_change_percent",
        cell_class=PercentCell,
        style_fn=_get_style_for_value,
    ),
    ColumnSpec(
        "_52w_range",
        "52w Range",
        "52-Week Range",
        20,
        attr_name="fifty_two_week_range",
    ),
    ColumnSpec(
        "_52w_change_percent",
        "52w Chg%",
        "52-Week Change Percent",
        9,
        attr_name="fifty_two_week_change_percent",
        cell_class=PercentCell,
        style_fn=_get_style_for_value,
    ),
    # === Moving Averages ===
    ColumnSpec(
        "_50d_avg",
        "50d Avg",
        "50-Day Average",
        10,
        attr_name="fifty_day_average",
    ),
    ColumnSpec(
        "_50d_avg_change",
        "50d Chg",
        "50-Day Average Change",
        10,
        attr_name="fifty_day_average_change",
        style_fn=_get_style_for_value,
    ),
    ColumnSpec(
        "_50d_avg_change_percent",
        "50d %",
        "50-Day Average Change Percent",
        8,
        attr_name="fifty_day_average_change_percent",
        cell_class=PercentCell,
        style_fn=_get_style_for_value,
    ),
    ColumnSpec(
        "_200d_avg",
        "200d Avg",
        "200-Day Average",
        10,
        attr_name="two_hundred_day_average",
    ),
    ColumnSpec(
        "_200d_avg_change",
        "200d Chg",
        "200-Day Average Change",
        10,
        attr_name="two_hundred_day_average_change",
        style_fn=_get_style_for_value,
    ),
    ColumnSpec(
        "_200d_avg_change_percent",
        "200d %",
        "200-Day Average Change Percent",
        8,
        attr_name="two_hundred_day_average_change_percent",
        cell_class=PercentCell,
        style_fn=_get_style_for_value,
    ),
    # === Volume ===
    ColumnSpec(
        "volume",
        "Volume",
        "Market Volume",
        10,
        attr_name="regular_market_volume",
    ),
    ColumnSpec(
        "avg_volume_10d",
        "Avg Vol 10d",
        "Average Daily Volume (10 Day)",
        11,
        attr_name="average_daily_volume_10_day",
    ),
    ColumnSpec(
        "avg_volume",
        "Avg Vol",
        "Average Daily Volume (3 Month)",
        10,
        attr_name="average_daily_volume_3_month",
    ),
    # === Bid/Ask ===
    ColumnSpec("bid", "Bid", "Bid Price", 10),
    ColumnSpec("bid_size", "Bid Size", "Bid Size", 10),
    ColumnSpec("ask", "Ask", "Ask Price", 10),
    ColumnSpec("ask_size", "Ask Size", "Ask Size", 10),
    # === Valuation Metrics ===
    ColumnSpec(
        "pe", "P/E", "Trailing Price-to-Earnings Ratio", 8, attr_name="trailing_pe"
    ),
    ColumnSpec("forward_pe", "Fwd P/E", "Forward Price-to-Earnings Ratio", 8),
    ColumnSpec(
        "price_eps_current_year",
        "P/E CY",
        "Price-to-Earnings Current Year",
        8,
    ),
    ColumnSpec("price_to_book", "P/B", "Price-to-Book Ratio", 8),
    ColumnSpec("book_value", "Book Val", "Book Value", 10),
    ColumnSpec("market_cap", "Mkt Cap", "Market Capitalization", 10),
    # === Earnings ===
    ColumnSpec(
        "eps_ttm",
        "EPS TTM",
        "Earnings Per Share (Trailing Twelve Months)",
        10,
        attr_name="eps_trailing_twelve_months",
    ),
    ColumnSpec("eps_current_year", "EPS CY", "Earnings Per Share (Current Year)", 10),
    ColumnSpec("eps_forward", "EPS Fwd", "Earnings Per Share (Forward)", 10),
    ColumnSpec("earnings_datetime", "Earnings", "Earnings Announcement Datetime", 16),
    ColumnSpec(
        "earnings_datetime_start",
        "Earn Start",
        "Earnings Announcement Start",
        16,
    ),
    ColumnSpec("earnings_datetime_end", "Earn End", "Earnings Announcement End", 16),
    # === Dividends ===
    ColumnSpec(
        "dividend_yield",
        "Div Yld",
        "Dividend Yield",
        8,
        cell_class=PercentCell,
    ),
    ColumnSpec("dividend_rate", "Div Rate", "Dividend Rate", 10),
    ColumnSpec("dividend_date", "Div Date", "Dividend Date", 10),
    ColumnSpec(
        "trailing_annual_dividend_rate",
        "Tr Div Rate",
        "Trailing Annual Dividend Rate",
        11,
    ),
    ColumnSpec(
        "trailing_annual_dividend_yield",
        "Tr Div Yld",
        "Trailing Annual Dividend Yield",
        10,
        cell_class=PercentCell,
    ),
    # === ETF/Mutual Fund Specific ===
    ColumnSpec("net_assets", "Net Assets", "Net Assets", 12),
    ColumnSpec(
        "net_expense_ratio",
        "Exp Ratio",
        "Net Expense Ratio",
        9,
        cell_class=PercentCell,
    ),
    ColumnSpec(
        "ytd_return", "YTD Ret", "Year-to-Date Return", 9, cell_class=PercentCell
    ),
    ColumnSpec(
        "trailing_three_month_returns",
        "3M Ret",
        "Trailing 3-Month Returns",
        8,
        cell_class=PercentCell,
    ),
    ColumnSpec(
        "trailing_three_month_nav_returns",
        "3M NAV Ret",
        "Trailing 3-Month NAV Returns",
        10,
        cell_class=PercentCell,
    ),
    # === Options Specific ===
    ColumnSpec("option_type", "Opt Type", "Option Type", 8),
    ColumnSpec("strike", "Strike", "Strike Price", 10),
    ColumnSpec("expire_date", "Exp Date", "Expiration Date", 10),
    ColumnSpec("open_interest", "Open Int", "Open Interest", 10),
    ColumnSpec("underlying_symbol", "Underlying", "Underlying Symbol", 10),
    ColumnSpec("underlying_short_name", "Und Name", "Underlying Short Name", 15),
    ColumnSpec(
        "head_symbol_as_string",
        "Head Sym",
        "Head Symbol",
        10,
    ),
    # === Futures Specific ===
    ColumnSpec(
        "underlying_exchange_symbol",
        "Und Exch",
        "Underlying Exchange Symbol",
        10,
    ),
    # === Cryptocurrency Specific ===
    ColumnSpec("from_currency", "From Ccy", "From Currency", 10),
    ColumnSpec("to_currency", "To Ccy", "To Currency", 10),
    ColumnSpec("last_market", "Last Mkt", "Last Market", 12),
    ColumnSpec("circulating_supply", "Circ Supply", "Circulating Supply", 12),
    ColumnSpec("volume_24_hr", "Vol 24h", "Volume (24 Hour)", 12),
    ColumnSpec(
        "volume_all_currencies",
        "Vol All Ccy",
        "Volume (All Currencies)",
        12,
    ),
    ColumnSpec("start_date", "Start Date", "Coin Start Date", 10),
    ColumnSpec("crypto_tradeable", "Crypto Trd", "Crypto Tradeable", 10),
    # === Exchange & Market Info ===
    ColumnSpec("exchange", "Exch", "Exchange", 6),
    ColumnSpec("full_exchange_name", "Exchange", "Full Exchange Name", 20),
    ColumnSpec("market", "Market", "Market", 8),
    ColumnSpec("market_state", "Mkt State", "Market State", 10),
    ColumnSpec("region", "Region", "Region", 6),
    ColumnSpec(
        "exchange_data_delayed_by",
        "Delay",
        "Exchange Data Delay (Minutes)",
        6,
    ),
    # === Pre/Post Market ===
    ColumnSpec("pre_market_price", "Pre Mkt", "Pre-Market Price", 10),
    ColumnSpec(
        "pre_market_change",
        "Pre Chg",
        "Pre-Market Change",
        10,
        style_fn=_get_style_for_value,
    ),
    ColumnSpec(
        "pre_market_change_percent",
        "Pre %",
        "Pre-Market Change Percent",
        8,
        cell_class=PercentCell,
        style_fn=_get_style_for_value,
    ),
    ColumnSpec("pre_market_datetime", "Pre Time", "Pre-Market Datetime", 16),
    ColumnSpec("post_market_price", "Post Mkt", "Post-Market Price", 10),
    ColumnSpec(
        "post_market_change",
        "Post Chg",
        "Post-Market Change",
        10,
        style_fn=_get_style_for_value,
    ),
    ColumnSpec(
        "post_market_change_percent",
        "Post %",
        "Post-Market Change Percent",
        8,
        cell_class=PercentCell,
        style_fn=_get_style_for_value,
    ),
    ColumnSpec("post_market_datetime", "Post Time", "Post-Market Datetime", 16),
    # === Shares & Ownership ===
    ColumnSpec("shares_outstanding", "Shares Out", "Shares Outstanding", 12),
    # === Ratings & Indicators ===
    ColumnSpec(
        "average_analyst_rating",
        "Analyst",
        "Average Analyst Rating",
        15,
    ),
    ColumnSpec("tradeable", "Tradeable", "Tradeable", 9),
    ColumnSpec("esg_populated", "ESG", "ESG Data Available", 5),
    # === Dates & Times ===
    ColumnSpec(
        "regular_market_datetime",
        "Mkt Time",
        "Regular Market Datetime",
        16,
    ),
    ColumnSpec(
        "first_trade_datetime",
        "First Trade",
        "First Trade Datetime",
        16,
    ),
    ColumnSpec("ipo_expected_date", "IPO Date", "Expected IPO Date", 10),
    ColumnSpec("name_change_date", "Name Chg", "Name Change Date", 10),
    ColumnSpec("prev_name", "Prev Name", "Previous Name", 20),
]
"""
Declare specifications for all available quote columns.

Convert each ColumnSpec to a QuoteColumn via _build_column().
Populate ALL_QUOTE_COLUMNS with the resulting columns.

### YQuote fields NOT included as columns

#### Raw timestamp fields (computed datetime versions exist)
- `earnings_timestamp` - Use `earnings_datetime` instead
- `earnings_timestamp_start` - Use `earnings_datetime_start` instead
- `earnings_timestamp_end` - Use `earnings_datetime_end` instead
- `regular_market_time` - Use `regular_market_datetime` instead
- `post_market_time` - Use `post_market_datetime` instead
- `pre_market_time` - Use `pre_market_datetime` instead
- `first_trade_date_milliseconds` - Use `first_trade_datetime` instead

#### URL fields (no value in displaying URLs in a table)
- `coin_image_url` - Image URL for cryptocurrency
- `coin_market_cap_link` - URL to CoinMarketCap site
- `logo_url` - Company logo URL

#### Internal/Technical fields (not meaningful to users)
- `custom_price_alert_confidence` - Yahoo internal field with unclear meaning
- `message_board_id` - Yahoo message board identifier
- `gmt_off_set_milliseconds` - Technical timezone offset
- `source_interval` - Data source update interval
- `price_hint` - Internal decimal precision indicator
- `triggerable` - Internal Yahoo flag with undocumented purpose
- `language` - Language code (e.g., "en-US"), not typically useful in watchlist

#### Duplicate/Redundant information
- `expire_iso_date` - ISO format of expiration date; `expire_date` is sufficient
- `exchange_timezone_name` - Full timezone name; exchange info is more useful
- `exchange_timezone_short_name` - Short timezone; same reason
- `type_disp` - Display version of quote_type; `quote_type` already provides this
- `contract_symbol` - Boolean flag; `underlying_symbol` provides more useful info
"""

ALL_QUOTE_COLUMNS: Final[dict[str, QuoteColumn]] = {
    spec.key: _build_column(spec) for spec in COLUMN_SPECS
}
"""
A dictionary that contains QuoteColumns available for the quote table.

Each QuoteColumn is keyed by its key name.
"""
