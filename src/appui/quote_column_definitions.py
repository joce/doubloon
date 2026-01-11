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

        return cell_class(value, **kwargs)  # type: ignore[call-arg]

    return quote_column(
        spec.short_name,
        full_name=spec.full_name,
        width=spec.width,
        key=spec.key,
        justification=justify,
        cell_factory=cell_factory,
    )


COLUMN_SPECS: Final[list[ColumnSpec]] = [
    ColumnSpec(
        "ticker",
        "Ticker",
        "Ticker Symbol",
        8,
        attr_name="symbol",
        cell_class=TickerCell,
    ),
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
        "volume",
        "Volume",
        "Market Volume",
        10,
        attr_name="regular_market_volume",
    ),
    ColumnSpec(
        "avg_volume",
        "Avg Vol",
        "Average Daily Volume (3 Month)",
        10,
        attr_name="average_daily_volume_3_month",
    ),
    ColumnSpec(
        "pe", "P/E", "Trailing Price-to-Earnings Ratio", 6, attr_name="trailing_pe"
    ),
    ColumnSpec("dividend", "Div", "Dividend Yield", 6, attr_name="dividend_yield"),
    ColumnSpec("market_cap", "Mkt Cap", "Market Capitalization", 10),
    ColumnSpec("dividend_date", "Div Date", "Dividend Date", 10),
    ColumnSpec("market_state", "Mkt State", "Market State", 10),
    ColumnSpec("option_type", "Opt Type", "Option Type", 8),
    ColumnSpec("quote_type", "Type", "Quote Type", 15),
    ColumnSpec("tradeable", "Tradeable", "Tradeable", 9),
    ColumnSpec("post_market_datetime", "Post Mkt", "Post-Market Datetime", 16),
]
"""
Declare specifications for all available quote columns.

Convert each ColumnSpec to a QuoteColumn via _build_column().
Populate ALL_QUOTE_COLUMNS with the resulting columns.
"""

ALL_QUOTE_COLUMNS: Final[dict[str, QuoteColumn]] = {
    spec.key: _build_column(spec) for spec in COLUMN_SPECS
}
"""
A dictionary that contains QuoteColumns available for the quote table.

Each QuoteColumn is keyed by its key name.
"""
