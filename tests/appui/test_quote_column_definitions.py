"""Tests for quote column definitions and cell types."""

# pyright: reportPrivateUsage=none
# pylint: disable=redefined-outer-name
# pylint: disable=missing-return-doc

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from appui.enums import Justify
from appui.quote_column_definitions import (
    _GAINING_COLOR,
    _LOSING_COLOR,
    ALL_QUOTE_COLUMNS,
    COLUMN_SPECS,
    TICKER_COLUMN_KEY,
    BooleanCell,
    ColumnSpec,
    CompactNumberCell,
    DateCell,
    DateTimeCell,
    EnumCell,
    FloatCell,
    PercentCell,
    TextCell,
    TickerCell,
    _build_column,
    _get_field_type,
    _get_style_for_value,
    _with_secondary_key,
)
from calahan.enums import MarketState, OptionType, QuoteType
from calahan.yquote import YQuote

# -- Tests for _with_secondary_key --


def test_with_secondary_key_none_returns_single_tuple() -> None:
    """Return single-element tuple when secondary_key is None."""

    result = _with_secondary_key(42.0, None)
    assert result == (42.0,)


def test_with_secondary_key_provided_returns_two_tuple() -> None:
    """Return two-element tuple when secondary_key is provided."""

    result = _with_secondary_key(42.0, "AAPL")
    assert result == (42.0, "AAPL")


def test_with_secondary_key_empty_returns_single_tuple() -> None:
    """Empty string secondary_key still produces single-element tuple."""

    result = _with_secondary_key(42.0, "")
    assert result == (42.0,)


# -- Tests for TextCell --


def test_text_cell_basic_defaults() -> None:
    """Create text cell with default options."""

    cell = TextCell("Hello")
    assert cell.text == "Hello"
    assert cell.justification == Justify.LEFT
    assert cell.sort_key == ("hello",)


def test_text_cell_case_sensitive_sort() -> None:
    """Case-sensitive sorting preserves original case in sort key."""

    cell = TextCell("Hello", case_sensitive=True)
    assert cell.sort_key == ("Hello",)


def test_text_cell_case_insensitive_sort() -> None:
    """Case-insensitive sorting lowercases sort key."""

    cell = TextCell("HELLO", case_sensitive=False)
    assert cell.sort_key == ("hello",)


def test_text_cell_with_secondary_key() -> None:
    """Secondary key appears in sort key tuple."""

    cell = TextCell("Alpha", secondary_key="AAPL")
    assert cell.sort_key == ("alpha", "aapl")


def test_text_cell_secondary_key_case_sensitive() -> None:
    """Case-sensitive secondary key preserved in sort key."""

    cell = TextCell("Alpha", secondary_key="AAPL", case_sensitive=True)
    assert cell.sort_key == ("Alpha", "AAPL")


def test_text_cell_custom_justification() -> None:
    """Custom justification is applied."""

    cell = TextCell("Test", justification=Justify.RIGHT)
    assert cell.justification == Justify.RIGHT


def test_text_cell_custom_style() -> None:
    """Custom style is applied."""

    cell = TextCell("Test", style="bold red")
    assert cell.style == "bold red"


# -- Tests for TickerCell --


def test_ticker_cell_uppercase_conversion() -> None:
    """Ticker symbol is converted to upper case."""

    cell = TickerCell("aapl")
    assert cell.text == "AAPL"


def test_ticker_cell_empty_symbol() -> None:
    """Empty symbol is handled gracefully."""

    cell = TickerCell("")
    assert not cell.text


def test_ticker_cell_none_symbol() -> None:
    """None symbol handled as empty string."""

    cell = TickerCell(None)  # type: ignore[arg-type]
    assert not cell.text


def test_ticker_cell_sort_key_lowercase() -> None:
    """Sort key is lowercase regardless of input."""

    cell = TickerCell("AAPL")
    assert cell.sort_key == ("aapl",)


def test_ticker_cell_default_justification() -> None:
    """Default justification is LEFT."""

    cell = TickerCell("AAPL")
    assert cell.justification == Justify.LEFT


# -- Tests for FloatCell --


def test_float_cell_basic() -> None:
    """Format float with default precision."""

    cell = FloatCell(123.456)
    assert cell.text == "123.46"
    assert cell.justification == Justify.RIGHT


def test_float_cell_custom_precision() -> None:
    """Format float with custom precision."""

    cell = FloatCell(123.456789, precision=4)
    assert cell.text == "123.4568"


def test_float_cell_none_value() -> None:
    """None value shows N/A and sorts to bottom."""

    cell = FloatCell(None)
    assert cell.text == "N/A"
    assert cell.sort_key == (float("-inf"),)


def test_float_cell_sort_key() -> None:
    """Sort key contains the float value."""

    cell = FloatCell(42.5)
    assert cell.sort_key == (42.5,)


def test_float_cell_with_secondary_key() -> None:
    """Secondary key appears in sort key."""

    cell = FloatCell(100.0, secondary_key="AAPL")
    assert cell.sort_key == (100.0, "AAPL")


def test_float_cell_with_style() -> None:
    """Custom style is applied."""

    cell = FloatCell(50.0, style="#00FF00")
    assert cell.style == "#00FF00"


# -- Tests for PercentCell --


def test_percent_cell_basic() -> None:
    """Format value as percentage."""

    cell = PercentCell(12.34)
    assert cell.text == "12.34%"
    assert cell.justification == Justify.RIGHT


def test_percent_cell_none_value() -> None:
    """None value shows N/A and sorts to bottom."""

    cell = PercentCell(None)
    assert cell.text == "N/A"
    assert cell.sort_key == (float("-inf"),)


def test_percent_cell_negative() -> None:
    """Negative percentages formatted correctly."""

    cell = PercentCell(-5.67)
    assert cell.text == "-5.67%"


def test_percent_cell_with_secondary_key() -> None:
    """Secondary key appears in sort key."""

    cell = PercentCell(10.0, secondary_key="MSFT")
    assert cell.sort_key == (10.0, "MSFT")


# -- Tests for CompactNumberCell --


def test_compact_number_cell_small() -> None:
    """Small numbers shown without suffix."""

    cell = CompactNumberCell(999)
    assert cell.text == "999"


def test_compact_number_cell_thousands() -> None:
    """Thousands shown with K suffix."""

    cell = CompactNumberCell(1500)
    assert cell.text == "1.50K"


def test_compact_number_cell_millions() -> None:
    """Millions shown with M suffix."""

    cell = CompactNumberCell(2500000)
    assert cell.text == "2.50M"


def test_compact_number_cell_none() -> None:
    """None value shows N/A and sorts to bottom."""

    cell = CompactNumberCell(None)
    assert cell.text == "N/A"
    assert cell.sort_key == (float("-inf"),)


def test_compact_number_cell_default_justification() -> None:
    """Default justification is RIGHT."""

    cell = CompactNumberCell(100)
    assert cell.justification == Justify.RIGHT


def test_compact_number_cell_with_secondary_key() -> None:
    """Secondary key appears in sort key."""

    cell = CompactNumberCell(1000, secondary_key="GOOG")
    assert cell.sort_key == (1000, "GOOG")


# -- Tests for DateCell --


def test_date_cell_basic() -> None:
    """Format date with default format."""

    cell = DateCell(date(2024, 6, 15))
    assert cell.text == "2024-06-15"
    assert cell.justification == Justify.LEFT


def test_date_cell_custom_format() -> None:
    """Format date with custom format string."""

    cell = DateCell(date(2024, 6, 15), date_format="%m/%d/%Y")
    assert cell.text == "06/15/2024"


def test_date_cell_none_value() -> None:
    """None value shows N/A and sorts to bottom."""

    cell = DateCell(None)
    assert cell.text == "N/A"
    assert cell.sort_key == (float("-inf"),)


def test_date_cell_sort_key_ordinal() -> None:
    """Sort key uses date ordinal for correct ordering."""

    d = date(2024, 6, 15)
    cell = DateCell(d)
    assert cell.sort_key == (d.toordinal(),)


def test_date_cell_with_secondary_key() -> None:
    """Secondary key appears in sort key."""

    d = date(2024, 1, 1)
    cell = DateCell(d, secondary_key="NVDA")
    assert cell.sort_key == (d.toordinal(), "NVDA")


# -- Tests for DateTimeCell --


def test_datetime_cell_basic() -> None:
    """Format datetime with default format."""

    dt = datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc)
    cell = DateTimeCell(dt)
    assert cell.text == "2024-06-15 14:30"
    assert cell.justification == Justify.LEFT


def test_datetime_cell_custom_format() -> None:
    """Format datetime with custom format string."""

    dt = datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc)
    cell = DateTimeCell(dt, datetime_format="%Y/%m/%d %H:%M:%S")
    assert cell.text == "2024/06/15 14:30:00"


def test_datetime_cell_none_value() -> None:
    """None value shows N/A and sorts to bottom."""

    cell = DateTimeCell(None)
    assert cell.text == "N/A"
    assert cell.sort_key == (float("-inf"),)


def test_datetime_cell_sort_key_timestamp() -> None:
    """Sort key uses timestamp for correct ordering."""

    dt = datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc)
    cell = DateTimeCell(dt)
    assert cell.sort_key == (dt.timestamp(),)


def test_datetime_cell_with_secondary_key() -> None:
    """Secondary key appears in sort key."""

    dt = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    cell = DateTimeCell(dt, secondary_key="AMD")
    assert cell.sort_key == (dt.timestamp(), "AMD")


# -- Tests for EnumCell --


def test_enum_cell_basic() -> None:
    """Format enum value as title case."""

    cell = EnumCell(MarketState.REGULAR)
    assert cell.text == "Regular"
    assert cell.justification == Justify.LEFT


def test_enum_cell_underscore() -> None:
    """Enum with underscores formatted with spaces."""

    cell = EnumCell(QuoteType.PRIVATE_COMPANY)
    assert cell.text == "Private Company"


def test_enum_cell_none_value() -> None:
    """None value shows N/A."""

    cell = EnumCell(None)
    assert cell.text == "N/A"
    assert cell.sort_key == ("",)


def test_enum_cell_sort_key_lowercase() -> None:
    """Sort key uses lowercase for case-insensitive sorting."""

    cell = EnumCell(MarketState.PRE)
    assert cell.sort_key == ("pre",)


def test_enum_cell_with_secondary_key() -> None:
    """Secondary key appears in sort key."""

    cell = EnumCell(OptionType.CALL, secondary_key="SPY")
    assert cell.sort_key == ("call", "spy")


# -- Tests for BooleanCell --


def test_boolean_cell_true() -> None:
    """True renders as checked checkbox."""

    cell = BooleanCell(value=True)
    assert cell.text == "☑"
    assert cell.justification == Justify.CENTER


def test_boolean_cell_false() -> None:
    """False renders as unchecked checkbox."""

    cell = BooleanCell(value=False)
    assert cell.text == "☐"


def test_boolean_cell_none() -> None:
    """None value shows N/A and sorts to bottom."""

    cell = BooleanCell(None)
    assert cell.text == "N/A"
    assert cell.sort_key == (float("-inf"),)


def test_boolean_cell_sort_ordering() -> None:
    """Sort keys order: None < False < True."""

    none_cell = BooleanCell(None)
    false_cell = BooleanCell(value=False)
    true_cell = BooleanCell(value=True)
    assert none_cell.sort_key < false_cell.sort_key < true_cell.sort_key


def test_boolean_cell_with_secondary_key() -> None:
    """Secondary key appears in sort key."""

    cell = BooleanCell(value=True, secondary_key="TSLA")
    assert cell.sort_key == (1.0, "TSLA")


# -- Tests for _get_style_for_value --


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(10.5, _GAINING_COLOR, id="positive"),
        pytest.param(0.001, _GAINING_COLOR, id="small-positive"),
        pytest.param(-5.2, _LOSING_COLOR, id="negative"),
        pytest.param(-0.001, _LOSING_COLOR, id="small-negative"),
        pytest.param(0.0, "", id="zero"),
    ],
)
def test_get_style_for_value(value: float, expected: str) -> None:
    """Return appropriate color based on value sign."""

    assert _get_style_for_value(value) == expected


# -- Tests for ColumnSpec --


def test_column_spec_basic() -> None:
    """Create spec with required fields only."""

    expected_width = 10
    spec = ColumnSpec("test", "Test", "Test Column", expected_width)
    assert spec.key == "test"
    assert spec.short_name == "Test"
    assert spec.full_name == "Test Column"
    assert spec.width == expected_width
    assert spec.attr_name is None
    assert spec.precision is None
    assert spec.style_fn is None
    assert spec.cell_class is None


def test_column_spec_full() -> None:
    """Create spec with all optional fields."""

    expected_precision = 4

    def style_fn(_: float) -> str:
        return "#FF0000"

    spec = ColumnSpec(
        "price",
        "Price",
        "Market Price",
        12,
        attr_name="regular_market_price",
        precision=expected_precision,
        style_fn=style_fn,
        cell_class=FloatCell,
    )
    assert spec.attr_name == "regular_market_price"
    assert spec.precision == expected_precision
    assert spec.style_fn is style_fn
    assert spec.cell_class is FloatCell


def test_column_spec_frozen() -> None:
    """ColumnSpec is immutable."""

    spec = ColumnSpec("key", "Label", "Full Name", 8)
    with pytest.raises(AttributeError):
        spec.key = "new_key"  # type: ignore[misc]


# -- Tests for _get_field_type --


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        pytest.param(str, str, id="str"),
        pytest.param(int, int, id="int"),
        pytest.param(float, float, id="float"),
        pytest.param(str | None, str, id="optional-str"),
        pytest.param(float | None, float, id="optional-float"),
        pytest.param(int | None, int, id="union-int"),
        pytest.param(MarketState, MarketState, id="enum"),
    ],
)
def test_get_field_type(annotation: object, expected: type) -> None:
    """Extract actual type from annotations."""

    assert _get_field_type(annotation) is expected


# -- Tests for _build_column --


def test_build_column_ticker() -> None:
    """Build ticker column with TickerCell."""

    expected_width = 8
    spec = ColumnSpec(
        "ticker", "Ticker", "Ticker Symbol", expected_width, attr_name="symbol"
    )
    column = _build_column(spec)
    assert column.key == "ticker"
    assert column.label == "Ticker"
    assert column.width == expected_width
    assert column.justification == Justify.LEFT


def test_build_column_float() -> None:
    """Build float column with FloatCell."""

    spec = ColumnSpec(
        "price", "Price", "Market Price", 10, attr_name="regular_market_price"
    )
    column = _build_column(spec)
    assert column.key == "price"
    assert column.justification == Justify.RIGHT


def test_build_column_int() -> None:
    """Build int column with CompactNumberCell."""

    spec = ColumnSpec(
        "volume", "Volume", "Market Volume", 10, attr_name="regular_market_volume"
    )
    column = _build_column(spec)
    assert column.key == "volume"
    assert column.justification == Justify.RIGHT


def test_build_column_bool() -> None:
    """Build bool column with BooleanCell."""

    spec = ColumnSpec(
        "tradeable", "Tradeable", "Is Tradeable", 9, attr_name="tradeable"
    )
    column = _build_column(spec)
    assert column.key == "tradeable"
    assert column.justification == Justify.CENTER


def test_build_column_date() -> None:
    """Build date column with DateCell."""

    spec = ColumnSpec(
        "div_date", "Div Date", "Dividend Date", 10, attr_name="dividend_date"
    )
    column = _build_column(spec)
    assert column.key == "div_date"
    assert column.justification == Justify.LEFT


def test_build_column_datetime() -> None:
    """Build datetime column with DateTimeCell via computed field."""

    spec = ColumnSpec(
        "post_market",
        "Post Mkt",
        "Post Market Time",
        16,
        attr_name="post_market_datetime",
    )
    column = _build_column(spec)
    assert column.key == "post_market"
    assert column.justification == Justify.LEFT


def test_build_column_enum() -> None:
    """Build enum column with EnumCell."""

    spec = ColumnSpec(
        "market_state", "Mkt State", "Market State", 10, attr_name="market_state"
    )
    column = _build_column(spec)
    assert column.key == "market_state"
    assert column.justification == Justify.LEFT


def test_build_column_explicit_cell_class() -> None:
    """Override cell class via spec."""

    spec = ColumnSpec(
        "change_pct",
        "Chg %",
        "Change Percent",
        8,
        attr_name="regular_market_change_percent",
        cell_class=PercentCell,
    )
    column = _build_column(spec)
    assert column.justification == Justify.RIGHT


def test_build_column_invalid_field() -> None:
    """Raise ValueError for non-existent YQuote field."""

    spec = ColumnSpec(
        "invalid", "Invalid", "Invalid Field", 10, attr_name="no_such_field"
    )
    with pytest.raises(ValueError, match="Field no_such_field not found"):
        _build_column(spec)


def test_build_column_key_defaults_to_attr_name() -> None:
    """Attr name defaults to key when not specified."""

    spec = ColumnSpec("tradeable", "Trade", "Tradeable", 9)
    column = _build_column(spec)
    assert column.key == "tradeable"


# -- Tests for ALL_QUOTE_COLUMNS and COLUMN_SPECS --


def test_all_specs_have_columns() -> None:
    """Every spec in COLUMN_SPECS has a corresponding column."""

    for spec in COLUMN_SPECS:
        assert spec.key in ALL_QUOTE_COLUMNS


def test_column_count_matches_specs() -> None:
    """Number of columns matches number of specs."""

    assert len(ALL_QUOTE_COLUMNS) == len(COLUMN_SPECS)


def test_ticker_column_key_exists() -> None:
    """Ticker column is present."""

    assert TICKER_COLUMN_KEY in ALL_QUOTE_COLUMNS


@pytest.mark.parametrize(
    "key",
    ["ticker", "last", "change", "change_percent", "volume"],
)
def test_essential_columns_exist(key: str) -> None:
    """Core financial columns are defined."""

    assert key in ALL_QUOTE_COLUMNS


@pytest.mark.parametrize(
    "key",
    [spec.key for spec in COLUMN_SPECS],
    ids=[spec.key for spec in COLUMN_SPECS],
)
def test_column_has_cell_factory(key: str) -> None:
    """Every column has a cell factory defined."""

    column = ALL_QUOTE_COLUMNS[key]
    assert column.cell_factory is not None


# -- Integration tests for cell factories with YQuote data --


@pytest.fixture
def sample_quote() -> YQuote:
    """Load a real YQuote from test data for integration tests."""

    test_data_path = Path(__file__).parent.parent / "test_yquote.json"
    json_data = json.loads(test_data_path.read_text(encoding="utf-8"))
    # Return the first quote (AAPL)
    return YQuote.model_validate(json_data["quoteResponse"]["result"][0])


def test_ticker_cell_factory(sample_quote: YQuote) -> None:
    """Ticker cell factory produces TickerCell."""

    column = ALL_QUOTE_COLUMNS["ticker"]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert isinstance(cell, TickerCell)
    assert cell.text == "AAPL"


def test_float_cell_factory(sample_quote: YQuote) -> None:
    """Float cell factory produces FloatCell."""

    column = ALL_QUOTE_COLUMNS["last"]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert isinstance(cell, FloatCell)
    assert "182" in cell.text  # AAPL price from test data


def test_percent_cell_factory(sample_quote: YQuote) -> None:
    """Percent cell factory produces PercentCell."""

    column = ALL_QUOTE_COLUMNS["change_percent"]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert isinstance(cell, PercentCell)
    assert "%" in cell.text


def test_volume_cell_factory(sample_quote: YQuote) -> None:
    """Volume cell factory produces CompactNumberCell."""

    column = ALL_QUOTE_COLUMNS["volume"]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert isinstance(cell, CompactNumberCell)
    assert "M" in cell.text  # 43.76M from test data


def test_bool_cell_factory(sample_quote: YQuote) -> None:
    """Bool cell factory produces BooleanCell."""

    column = ALL_QUOTE_COLUMNS["tradeable"]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert isinstance(cell, BooleanCell)
    assert cell.text == "☐"  # tradeable=false in test data


def test_enum_cell_factory(sample_quote: YQuote) -> None:
    """Enum cell factory produces EnumCell."""

    column = ALL_QUOTE_COLUMNS["market_state"]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert isinstance(cell, EnumCell)
    assert cell.text == "Regular"


def test_change_column_style(sample_quote: YQuote) -> None:
    """Change column applies style based on value sign."""

    column = ALL_QUOTE_COLUMNS["change"]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert cell.style == _GAINING_COLOR


def test_change_percent_column_style(sample_quote: YQuote) -> None:
    """Change percent column applies style based on value sign."""

    column = ALL_QUOTE_COLUMNS["change_percent"]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert cell.style == _GAINING_COLOR


def test_secondary_key_is_symbol(sample_quote: YQuote) -> None:
    """Cells use symbol as secondary sort key."""

    column = ALL_QUOTE_COLUMNS["last"]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert "AAPL" in cell.sort_key


# -- Tests for cell comparison and sorting behavior --


def test_float_cells_sort_numerically() -> None:
    """FloatCells sort numerically."""

    low = FloatCell(10.0)
    high = FloatCell(20.0)
    assert low < high


def test_none_sorts_lowest() -> None:
    """None values sort below all real values."""

    none_cell = FloatCell(None)
    value_cell = FloatCell(-1000000.0)
    assert none_cell < value_cell


def test_text_cells_sort_case_insensitive() -> None:
    """TextCells sort case-insensitively by default."""

    upper = TextCell("ZEBRA")
    lower = TextCell("alpha")
    assert lower < upper  # 'a' < 'z'


def test_secondary_key_breaks_ties() -> None:
    """Secondary key used when primary values equal."""

    cell_a = FloatCell(100.0, secondary_key="AAAA")
    cell_b = FloatCell(100.0, secondary_key="ZZZZ")
    assert cell_a < cell_b


def test_equal_cells() -> None:
    """Cells with same values are equal."""

    cell1 = FloatCell(42.0)
    cell2 = FloatCell(42.0)
    assert cell1 == cell2
