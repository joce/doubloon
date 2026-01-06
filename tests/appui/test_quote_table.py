"""Tests for quote table factories."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from appui.enhanced_data_table import (
    EnhancedColumn,
    EnhancedDataTable,
    EnhancedTableCell,
)
from appui.enums import Justify
from appui.quote_column_definitions import TextCell
from appui.quote_table import quote_column, quote_table

if TYPE_CHECKING:
    from calahan import YQuote


def test_quote_column_factory_uses_default_behavior() -> None:
    """Factory returns EnhancedColumn with sensible defaults."""

    column = quote_column("Label")

    class DummyQuote:
        """Minimal stub that mimics the quote type for factory tests."""

        def __str__(self) -> str:
            return "dummy"

    assert isinstance(column, EnhancedColumn)
    assert column.label == "Label"
    assert column.full_name == "Label"
    assert column.key == "Label"
    assert column.cell_factory is not None
    dummy_quote = cast("YQuote", DummyQuote())
    default_cell = column.cell_factory(dummy_quote)
    assert isinstance(default_cell, EnhancedTableCell)
    assert default_cell.text == "dummy"
    assert default_cell.sort_key == ("dummy",)


def test_quote_column_factory_applies_overrides() -> None:
    """Factory respects keyword overrides."""

    def factory(q: YQuote) -> EnhancedTableCell:
        return TextCell(str(q), justification=Justify.LEFT)

    test_width = 8

    column = quote_column(
        "Ticker",
        full_name="Ticker Symbol",
        width=test_width,
        key="ticker",
        justification=Justify.LEFT,
        cell_factory=factory,
    )

    assert column.width == test_width
    assert column.key == "ticker"
    assert column.justification is Justify.LEFT
    assert column.cell_factory is factory
    assert column.full_name == "Ticker Symbol"


def test_quote_table_factory_returns_enhanced_data_table() -> None:
    """Factory instantiates EnhancedDataTable specialized for quotes."""

    table = quote_table()

    assert isinstance(table, EnhancedDataTable)
