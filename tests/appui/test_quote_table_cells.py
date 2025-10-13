"""Tests covering enhanced table cell behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from rich.console import Console
from textual._context import active_app

from appui._enums import Justify
from appui._quote_column_definitions import CompactNumberCell, FloatCell, TickerCell
from appui.enhanced_data_table import EnhancedColumn, EnhancedDataTable

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

    cell_lower = TickerCell("aapl", justification=Justify.LEFT)
    cell_upper = TickerCell("AAPL", justification=Justify.LEFT)

    assert cell_lower == cell_upper
    assert str(cell_lower) == "AAPL"
