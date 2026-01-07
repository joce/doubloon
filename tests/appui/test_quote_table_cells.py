"""Tests covering enhanced table cell behavior."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, cast

import pytest
from rich.console import Console
from textual._context import active_app

from appui.enhanced_data_table import EnhancedColumn, EnhancedDataTable
from appui.enums import Justify
from appui.quote_column_definitions import (
    BooleanCell,
    CompactNumberCell,
    DateCell,
    DateTimeCell,
    EnhancedTableCell,
    EnumCell,
    FloatCell,
    PercentCell,
    TextCell,
    TickerCell,
)
from calahan.enums import QuoteType

if TYPE_CHECKING:
    from typing import Any

    from textual.app import App


def test_compact_number_cell_orders_large_values() -> None:
    """Compact number cells compare on their underlying numeric magnitude."""

    big = CompactNumberCell(1_900_000_000, secondary_key="ticker-b")
    small = CompactNumberCell(980_000_000, secondary_key="ticker-a")

    assert small < big
    assert str(big) == "1.90B"
    assert str(small) == "980.00M"


def test_float_cell_none_ranks_lowest() -> None:
    """Float cells treat None values as less than any numeric value."""

    missing = FloatCell(None)
    present = FloatCell(10.0)

    assert missing < present
    assert str(missing) == "N/A"


def test_enhanced_data_table_sort_uses_cell_ordering() -> None:
    """EnhancedDataTable sorts rows using the ordering provided by cells."""

    dummy_app = cast("App[Any]", type("DummyApp", (), {"console": Console()})())
    token = active_app.set(dummy_app)
    try:
        table: EnhancedDataTable[dict[str, int]] = EnhancedDataTable()
        column = EnhancedColumn[dict[str, int]](
            "Value",
            key="value",
            justification=Justify.RIGHT,
            cell_factory=lambda data: CompactNumberCell(data["value"]),
        )
        table.add_enhanced_column(column)

        table.add_row_data("small", {"value": 980_000_000})
        table.add_row_data("large", {"value": 1_900_000_000})

        table.sort("value")

        assert table.get_row_index("small") == 0
        assert table.get_row_index("large") == 1
    finally:
        active_app.reset(token)


def test_ticker_cell_is_case_insensitive() -> None:
    """Ticker cells compare ignoring case while preserving display."""

    cell_lower = TickerCell("aapl")
    cell_upper = TickerCell("AAPL")

    assert cell_lower == cell_upper
    assert str(cell_lower) == "AAPL"


def test_date_cell_none_ranks_lowest() -> None:
    """Date cells treat None as less than any valid date."""

    missing = DateCell(None)
    present = DateCell(date(2024, 1, 2))

    assert missing < present
    assert str(missing) == "N/A"


def test_datetime_cell_formats_and_sorts() -> None:
    """Datetime cells format values and rank None below valid datetimes."""

    missing = DateTimeCell(None)
    present = DateTimeCell(datetime(2024, 1, 2, 3, 4, tzinfo=timezone.utc))

    assert missing < present
    assert str(present) == "2024-01-02 03:04"


def test_enum_cell_title_cases_values() -> None:
    """Enum cells render title-cased labels with word separators."""

    cell = EnumCell(QuoteType.PRIVATE_COMPANY)

    assert str(cell) == "Private Company"


def test_enum_cell_none_ranks_lowest() -> None:
    """Enum cells treat None as less than populated values."""

    missing = EnumCell(None)
    present = EnumCell(QuoteType.ETF)

    assert missing < present


def test_boolean_cell_renders_checkboxes() -> None:
    """Boolean cells display checkbox glyphs and sort by truthiness."""

    checked = BooleanCell(value=True)
    unchecked = BooleanCell(value=False)
    missing = BooleanCell(value=None)

    assert str(checked) == "☑"
    assert str(unchecked) == "☐"
    assert str(missing) == "N/A"
    assert unchecked < checked
    assert missing < unchecked


@pytest.mark.parametrize(
    ("cell", "expected_justification"),
    [
        pytest.param(TextCell("Sample Text"), Justify.LEFT, id="TextCell"),
        pytest.param(TickerCell("AAPL"), Justify.LEFT, id="TickerCell"),
        pytest.param(FloatCell(123.45), Justify.RIGHT, id="FloatCell"),
        pytest.param(PercentCell(0.05), Justify.RIGHT, id="PercentCell"),
        pytest.param(
            CompactNumberCell(1_000_000), Justify.RIGHT, id="CompactNumberCell"
        ),
        pytest.param(DateCell(date(2024, 1, 2)), Justify.LEFT, id="DateCell"),
        pytest.param(
            DateTimeCell(datetime(2024, 1, 2, 3, 4, tzinfo=timezone.utc)),
            Justify.LEFT,
            id="DateTimeCell",
        ),
        pytest.param(
            EnumCell(QuoteType.PRIVATE_COMPANY),
            Justify.LEFT,
            id="EnumCell",
        ),
        pytest.param(BooleanCell(value=True), Justify.CENTER, id="BooleanCell"),
    ],
)
def test_cell_default_justification(
    cell: EnhancedTableCell,
    expected_justification: Justify,
) -> None:
    """All cell types have appropriate default justification."""

    assert cell.justification == expected_justification
