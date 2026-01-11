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


@pytest.mark.parametrize(
    ("value", "secondary", "expected"),
    [
        pytest.param(42.0, None, (42.0,), id="none-returns-single"),
        pytest.param(42.0, "AAPL", (42.0, "AAPL"), id="provided-returns-two"),
        pytest.param(42.0, "", (42.0,), id="empty-returns-single"),
    ],
)
def test_with_secondary_key(
    value: float, secondary: str | None, expected: tuple[object, ...]
) -> None:
    """Secondary key handling for sort tuples."""

    assert _with_secondary_key(value, secondary) == expected


# -- Parametrized tests for cell None handling --


@pytest.mark.parametrize(
    ("cell_class", "expected_sort_key"),
    [
        pytest.param(FloatCell, (float("-inf"),), id="float"),
        pytest.param(PercentCell, (float("-inf"),), id="percent"),
        pytest.param(CompactNumberCell, (float("-inf"),), id="compact"),
        pytest.param(DateCell, (float("-inf"),), id="date"),
        pytest.param(DateTimeCell, (float("-inf"),), id="datetime"),
        pytest.param(BooleanCell, (float("-inf"),), id="boolean"),
        pytest.param(EnumCell, ("",), id="enum"),
    ],
)
def test_cell_none_shows_na_and_sorts_low(
    cell_class: type, expected_sort_key: tuple[object, ...]
) -> None:
    """None value shows N/A and sorts to bottom."""

    cell = cell_class(None)
    assert cell.text == "N/A"
    assert cell.sort_key == expected_sort_key


# -- Parametrized tests for default justification --


@pytest.mark.parametrize(
    ("cell_class", "value", "expected_justification"),
    [
        pytest.param(TextCell, "text", Justify.LEFT, id="text"),
        pytest.param(TickerCell, "AAPL", Justify.LEFT, id="ticker"),
        pytest.param(FloatCell, 1.0, Justify.RIGHT, id="float"),
        pytest.param(PercentCell, 1.0, Justify.RIGHT, id="percent"),
        pytest.param(CompactNumberCell, 100, Justify.RIGHT, id="compact"),
        pytest.param(DateCell, date(2024, 1, 1), Justify.LEFT, id="date"),
        pytest.param(
            DateTimeCell,
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            Justify.LEFT,
            id="datetime",
        ),
        pytest.param(EnumCell, MarketState.REGULAR, Justify.LEFT, id="enum"),
        pytest.param(BooleanCell, True, Justify.CENTER, id="boolean"),
    ],
)
def test_cell_default_justification(
    cell_class: type, value: object, expected_justification: Justify
) -> None:
    """Cell types have correct default justification."""

    cell = cell_class(value)
    assert cell.justification == expected_justification


# -- Parametrized tests for secondary key in sort key --


@pytest.mark.parametrize(
    ("cell_class", "value", "secondary_key", "expected_sort_key"),
    [
        pytest.param(
            TextCell, "Alpha", "AAPL", ("alpha", "aapl"), id="text-case-insensitive"
        ),
        pytest.param(FloatCell, 100.0, "AAPL", (100.0, "AAPL"), id="float"),
        pytest.param(PercentCell, 10.0, "MSFT", (10.0, "MSFT"), id="percent"),
        pytest.param(CompactNumberCell, 1000, "GOOG", (1000, "GOOG"), id="compact"),
        pytest.param(
            DateCell,
            date(2024, 1, 1),
            "NVDA",
            (date(2024, 1, 1).toordinal(), "NVDA"),
            id="date",
        ),
        pytest.param(
            DateTimeCell,
            datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            "AMD",
            (datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc).timestamp(), "AMD"),
            id="datetime",
        ),
        pytest.param(EnumCell, OptionType.CALL, "SPY", ("call", "spy"), id="enum"),
        pytest.param(BooleanCell, True, "TSLA", (1.0, "TSLA"), id="boolean"),
    ],
)
def test_cell_secondary_key_in_sort(
    cell_class: type,
    value: object,
    secondary_key: str,
    expected_sort_key: tuple[object, ...],
) -> None:
    """Secondary key appears in sort key tuple."""

    cell = cell_class(value, secondary_key=secondary_key)
    assert cell.sort_key == expected_sort_key


# -- TextCell specific tests --


@pytest.mark.parametrize(
    ("case_sensitive", "secondary_key", "expected"),
    [
        pytest.param(True, None, ("Hello",), id="case-sensitive-no-secondary"),
        pytest.param(False, None, ("hello",), id="case-insensitive-no-secondary"),
        pytest.param(True, "AAPL", ("Hello", "AAPL"), id="case-sensitive-secondary"),
    ],
)
def test_text_cell_case_sensitivity(
    *, case_sensitive: bool, secondary_key: str | None, expected: tuple[str, ...]
) -> None:
    """Case sensitivity affects sort key."""

    cell = TextCell("Hello", case_sensitive=case_sensitive, secondary_key=secondary_key)
    assert cell.sort_key == expected


def test_text_cell_custom_justification() -> None:
    """Custom justification is applied."""

    cell = TextCell("Test", justification=Justify.RIGHT)
    assert cell.justification == Justify.RIGHT


def test_text_cell_custom_style() -> None:
    """Custom style is applied."""

    cell = TextCell("Test", style="bold red")
    assert cell.style == "bold red"


# -- TickerCell specific tests --


@pytest.mark.parametrize(
    ("symbol", "expected_text", "expected_sort_key"),
    [
        pytest.param("aapl", "AAPL", ("aapl",), id="lowercase-to-upper"),
        pytest.param("AAPL", "AAPL", ("aapl",), id="uppercase-preserved"),
        pytest.param("", "", ("",), id="empty"),
        pytest.param(None, "", ("",), id="none"),
    ],
)
def test_ticker_cell(
    symbol: str | None, expected_text: str, expected_sort_key: tuple[str, ...]
) -> None:
    """Ticker normalizes to uppercase with lowercase sort key."""

    cell = TickerCell(symbol)  # type: ignore[arg-type]
    assert cell.text == expected_text
    assert cell.sort_key == expected_sort_key


# -- FloatCell specific tests --


@pytest.mark.parametrize(
    ("value", "precision", "expected"),
    [
        pytest.param(123.456, None, "123.46", id="default-precision"),
        pytest.param(123.456789, 4, "123.4568", id="custom-precision"),
    ],
)
def test_float_cell_formatting(
    value: float, precision: int | None, expected: str
) -> None:
    """Float formats with specified precision."""

    cell = FloatCell(value, precision=precision) if precision else FloatCell(value)
    assert cell.text == expected


def test_float_cell_with_style() -> None:
    """Custom style is applied."""

    cell = FloatCell(50.0, style="#00FF00")
    assert cell.style == "#00FF00"


# -- PercentCell specific tests --


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(12.34, "12.34%", id="positive"),
        pytest.param(-5.67, "-5.67%", id="negative"),
    ],
)
def test_percent_cell_formatting(value: float, expected: str) -> None:
    """Percent formats with sign and suffix."""

    cell = PercentCell(value)
    assert cell.text == expected


# -- CompactNumberCell specific tests --


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(999, "999", id="small"),
        pytest.param(1500, "1.50K", id="thousands"),
        pytest.param(2500000, "2.50M", id="millions"),
    ],
)
def test_compact_number_cell_formatting(value: int, expected: str) -> None:
    """Compact numbers formatted with appropriate suffix."""

    cell = CompactNumberCell(value)
    assert cell.text == expected


# -- DateCell specific tests --


@pytest.mark.parametrize(
    ("date_format", "expected"),
    [
        pytest.param(None, "2024-06-15", id="default-format"),
        pytest.param("%m/%d/%Y", "06/15/2024", id="custom-format"),
    ],
)
def test_date_cell_formatting(date_format: str | None, expected: str) -> None:
    """Date formats with specified format string."""

    d = date(2024, 6, 15)
    cell = DateCell(d, date_format=date_format) if date_format else DateCell(d)
    assert cell.text == expected


def test_date_cell_sort_key_ordinal() -> None:
    """Sort key uses date ordinal for correct ordering."""

    d = date(2024, 6, 15)
    cell = DateCell(d)
    assert cell.sort_key == (d.toordinal(),)


# -- DateTimeCell specific tests --


@pytest.mark.parametrize(
    ("datetime_format", "expected"),
    [
        pytest.param(None, "2024-06-15 14:30", id="default-format"),
        pytest.param("%Y/%m/%d %H:%M:%S", "2024/06/15 14:30:00", id="custom-format"),
    ],
)
def test_datetime_cell_formatting(datetime_format: str | None, expected: str) -> None:
    """Datetime formats with specified format string."""

    dt = datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc)
    cell = (
        DateTimeCell(dt, datetime_format=datetime_format)
        if datetime_format
        else DateTimeCell(dt)
    )
    assert cell.text == expected


def test_datetime_cell_sort_key_timestamp() -> None:
    """Sort key uses timestamp for correct ordering."""

    dt = datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc)
    cell = DateTimeCell(dt)
    assert cell.sort_key == (dt.timestamp(),)


# -- EnumCell specific tests --


@pytest.mark.parametrize(
    ("value", "expected_text", "expected_sort_key"),
    [
        pytest.param(MarketState.REGULAR, "Regular", ("regular",), id="simple"),
        pytest.param(
            QuoteType.PRIVATE_COMPANY,
            "Private Company",
            ("private company",),
            id="underscore",
        ),
        pytest.param(MarketState.PRE, "Pre", ("pre",), id="short"),
    ],
)
def test_enum_cell(
    value: MarketState | QuoteType,
    expected_text: str,
    expected_sort_key: tuple[str, ...],
) -> None:
    """Enum formats as title case with lowercase sort key."""

    cell = EnumCell(value)
    assert cell.text == expected_text
    assert cell.sort_key == expected_sort_key


# -- BooleanCell specific tests --


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(True, "☑", id="true"),
        pytest.param(False, "☐", id="false"),
    ],
)
def test_boolean_cell_rendering(*, value: bool, expected: str) -> None:
    """Boolean renders as checkbox."""

    cell = BooleanCell(value=value)
    assert cell.text == expected


def test_boolean_cell_sort_ordering() -> None:
    """Sort keys order: None < False < True."""

    none_cell = BooleanCell(None)
    false_cell = BooleanCell(value=False)
    true_cell = BooleanCell(value=True)
    assert none_cell.sort_key < false_cell.sort_key < true_cell.sort_key


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


@pytest.mark.parametrize(
    ("key", "attr_name", "expected_justification"),
    [
        pytest.param("ticker", "symbol", Justify.LEFT, id="ticker"),
        pytest.param("price", "regular_market_price", Justify.RIGHT, id="float"),
        pytest.param("volume", "regular_market_volume", Justify.RIGHT, id="int"),
        pytest.param("tradeable", "tradeable", Justify.CENTER, id="bool"),
        pytest.param("div_date", "dividend_date", Justify.LEFT, id="date"),
        pytest.param(
            "post_market", "post_market_datetime", Justify.LEFT, id="datetime"
        ),
        pytest.param("market_state", "market_state", Justify.LEFT, id="enum"),
    ],
)
def test_build_column_type_inference(
    key: str, attr_name: str, expected_justification: Justify
) -> None:
    """Build column with correct justification based on type."""

    spec = ColumnSpec(key, "Label", "Full Name", 10, attr_name=attr_name)
    column = _build_column(spec)
    assert column.key == key
    assert column.justification == expected_justification


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
    return YQuote.model_validate(json_data["quoteResponse"]["result"][0])


@pytest.mark.parametrize(
    ("column_key", "cell_class", "text_contains"),
    [
        pytest.param("ticker", TickerCell, "AAPL", id="ticker"),
        pytest.param("last", FloatCell, "182", id="float"),
        pytest.param("change_percent", PercentCell, "%", id="percent"),
        pytest.param("volume", CompactNumberCell, "M", id="volume"),
        pytest.param("market_state", EnumCell, "Regular", id="enum"),
    ],
)
def test_cell_factory_produces_correct_type(
    sample_quote: YQuote, column_key: str, cell_class: type, text_contains: str
) -> None:
    """Cell factory produces expected cell type with expected text."""

    column = ALL_QUOTE_COLUMNS[column_key]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert isinstance(cell, cell_class)
    assert text_contains in cell.text


def test_bool_cell_factory(sample_quote: YQuote) -> None:
    """Bool cell factory produces BooleanCell with unchecked box."""

    column = ALL_QUOTE_COLUMNS["tradeable"]
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_quote)
    assert isinstance(cell, BooleanCell)
    assert cell.text == "☐"  # tradeable=false in test data


@pytest.mark.parametrize("column_key", ["change", "change_percent"])
def test_change_column_style(sample_quote: YQuote, column_key: str) -> None:
    """Change columns apply style based on value sign."""

    column = ALL_QUOTE_COLUMNS[column_key]
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

    assert FloatCell(10.0) < FloatCell(20.0)


def test_none_sorts_lowest() -> None:
    """None values sort below all real values."""

    assert FloatCell(None) < FloatCell(-1000000.0)


def test_text_cells_sort_case_insensitive() -> None:
    """TextCells sort case-insensitively by default."""

    assert TextCell("alpha") < TextCell("ZEBRA")


def test_secondary_key_breaks_ties() -> None:
    """Secondary key used when primary values equal."""

    cell_a = FloatCell(100.0, secondary_key="AAAA")
    cell_b = FloatCell(100.0, secondary_key="ZZZZ")
    assert cell_a < cell_b


def test_equal_cells() -> None:
    """Cells with same values are equal."""

    assert FloatCell(42.0) == FloatCell(42.0)
