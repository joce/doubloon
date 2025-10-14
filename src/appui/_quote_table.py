"""A data table widget to display and manipulate financial quotes."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, TypedDict

from calahan import YQuote

from .enhanced_data_table import EnhancedColumn, EnhancedDataTable, EnhancedTableCell

if TYPE_CHECKING:
    from collections.abc import Callable

    from ._enums import Justify

QuoteColumn: TypeAlias = EnhancedColumn[YQuote]
QuoteTable: TypeAlias = EnhancedDataTable[YQuote]


def quote_table() -> QuoteTable:
    """Create a QuoteTable.

    Returns:
        QuoteTable: An EnhancedDataTable specialized for YQuote.
    """

    return EnhancedDataTable[YQuote]()


def quote_column(
    # pylint: disable=unused-argument
    label: str,
    *,
    key: str | None = None,
    width: int | None = None,
    justification: Justify | None = None,
    cell_factory: Callable[[YQuote], EnhancedTableCell] | None = None,
    # pylint: enable=unused-argument
) -> QuoteColumn:
    """Create a QuoteColumn.

    Args:
        label (str): The display label for the column.
        key (str | None): The key to access the attribute in YQuote.
            Defaults to None, which uses the label as the key.
        width (int | None): The width of the column.
        justification (Justify | None): The text justification for the column.
        cell_factory (Callable[[YQuote], EnhancedTableCell] | None): Factory used
            to produce the cell object for each row.

    Returns:
        QuoteColumn: An EnhancedColumn specialized for YQuote.
    """

    class _QuoteColumnParams(TypedDict, total=False):
        """Typing helper for optional QuoteColumn parameters."""

        key: str
        width: int
        justification: Justify
        cell_factory: Callable[[YQuote], EnhancedTableCell]

    params: _QuoteColumnParams = {}
    if key is not None:
        params["key"] = key
    if width is not None:
        params["width"] = width
    if justification is not None:
        params["justification"] = justification
    if cell_factory is not None:
        params["cell_factory"] = cell_factory
    return EnhancedColumn[YQuote](label, **params)
