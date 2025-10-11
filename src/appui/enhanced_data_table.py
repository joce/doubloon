"""Enhanced DataTable widget with sorting and column ordering capabilities.

This module provides an enhanced version of Textual's DataTable widget with additional
features for data presentation and interaction. The `EnhancedDataTable` widget adds
support for customizable column formatting, interactive sorting with visual indicators,
and a keyboard-driven column ordering mode. It uses `EnhancedColumn` definitions to
specify column appearance, formatting functions, and sorting behavior, making it
suitable for displaying structured data with rich text formatting and interactive
sorting capabilities.
"""

from __future__ import annotations

import sys
from dataclasses import KW_ONLY, dataclass
from functools import total_ordering
from typing import TYPE_CHECKING, Callable, Generic, TypeVar

from rich.text import Text
from textual.binding import BindingsMap
from textual.reactive import Reactive, reactive
from textual.widgets import DataTable
from textual.widgets._data_table import ColumnKey  # noqa: PLC2701
from typing_extensions import Self

from ._enums import Justify, SortDirection
from ._messages import TableSortingChanged

if TYPE_CHECKING:
    from rich.style import Style
    from textual import events
    from textual._types import SegmentLines
    from textual.coordinate import Coordinate

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

T = TypeVar("T")
"""TypeVar for the data type that the table displays."""


@total_ordering
class EnhancedTableCell:
    """Rich-renderable table cell with an ordering key."""

    def __init__(
        self,
        sort_key: tuple[object, ...],
        text: str,
        justification: Justify = Justify.RIGHT,
        style: str = "",
    ) -> None:
        """Initialize an EnhancedTableCell.

        Args:
            sort_key (tuple[object, ...]): The tuple used to compare this cell with
                others.
            text (str): The text to display in the cell.
            justification (Justify): The justification of the cell.
            style (str): The style of the cell.
        """
        self._sort_key = sort_key
        self._text = text
        self._justification = justification
        self._style = style

    @property
    def sort_key(self) -> tuple[object, ...]:
        """Return the tuple used to compare this cell with others."""

        return self._sort_key

    @property
    def text(self) -> str:
        """Return the Rich text representation of the cell."""

        return self._text

    @property
    def justification(self) -> Justify:
        """Return the justification of the cell."""

        return self._justification

    @property
    def style(self) -> str:
        """Return the style of the cell."""

        return self._style

    def __rich__(self) -> Text:
        return Text(self._text, justify=self.justification.value, style=self.style)

    def __str__(self) -> str:
        return self._text

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(sort_key={self._sort_key!r}, text={self._text!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EnhancedTableCell):
            return NotImplemented
        return self.sort_key == other.sort_key

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, EnhancedTableCell):
            return NotImplemented
        return self.sort_key < other.sort_key

    def __hash__(self) -> int:
        return hash(self)


@dataclass(frozen=True)
class EnhancedColumn(Generic[T]):
    """Definition of an enhanced table column.

    Contains settings for the column's appearance (label, width, justification) and
    behavior (formatting, sorting, and sign indication).
    """

    label: str
    """The label of the column."""

    _: KW_ONLY

    width: int = 10
    """The width of the column."""

    key: str = None  # pyright: ignore[reportAssignmentType]
    """The key of the column, defaults to the label if omitted."""

    justification: Justify = Justify.RIGHT
    """Text justification for the column."""

    cell_factory: Callable[[T], EnhancedTableCell] | None = None
    """Factory that builds the cell objects for this column."""

    def __post_init__(self) -> None:
        """Ensure the column key defaults to the label when omitted."""

        if self.key is None:  # pyright: ignore[reportUnnecessaryComparison]
            object.__setattr__(self, "key", self.label)
        if self.cell_factory is None:
            object.__setattr__(
                self,
                "cell_factory",
                self._default_cell_factory,
            )

    def _default_cell_factory(self, data: T) -> EnhancedTableCell:
        """Declare a cell factory that renders the string representation of the data.

        Args:
            data (T): The data for the row.

        Returns:
            EnhancedTableCell: A cell containing the string representation of the data.
        """
        return EnhancedTableCell((str(data),), str(data), self.justification)


class EnhancedDataTable(DataTable[EnhancedTableCell], Generic[T]):
    """A DataTable with added capabilities."""

    _hovered_column: Reactive[int] = reactive(-1)

    def __init__(self) -> None:
        super().__init__()
        self._enhanced_columns: list[EnhancedColumn[T]] = []

        self._is_ordering: bool = False
        self._cursor_row: int = -1

        self._sort_column_key: str = ""
        self._sort_direction: SortDirection = SortDirection.ASCENDING

        # Bindings
        self._ordering_bindings: BindingsMap = BindingsMap()
        self._default_bindings: BindingsMap = BindingsMap()

        self._ordering_bindings.bind("right", "order_move_right", show=False)
        self._ordering_bindings.bind("left", "order_move_left", show=False)
        self._ordering_bindings.bind("enter", "order_select", show=False)

        # The following (especially the cursor type) need to be set after the binding
        # modes have been created
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.cursor_foreground_priority = "renderable"
        self.fixed_columns = 1

        #     def _update_table(self) -> None:
        #         """Update the table with the latest quotes (if any)."""

        #         if self._version == self._state.version:
        #             return

        #         # Set the column titles, including the sort arrow if needed
        #         quote_column: QuoteColumn
        #         for quote_column in self._state.quotes_columns:
        #             styled_column: Text = self._get_styled_column_title(quote_column)
        #             self.columns[self._column_key_map[quote_column.key]].label = styled_column

        #         quote_rows: list[QuoteRow] = self._state.quotes_rows

        #         i: int = 0
        #         quote: QuoteRow
        #         for quote in quote_rows:
        #             # We only use the index as the row key, so we can update and reorder the
        #             # rows as needed
        #             quote_key: RowKey = RowKey(str(i))
        #             i += 1
        #             # Update existing rows
        #             if quote_key in self.rows:
        #                 for j, cell in enumerate(quote.values):
        #                     self.update_cell(
        #                         quote_key,
        #                         self._state.quotes_columns[j].key,
        #                         QuoteTable._get_styled_cell(cell),
        #                     )
        #             else:
        #                 # Add new rows, if any
        #                 stylized_row: list[Text] = [
        #                     QuoteTable._get_styled_cell(cell) for cell in quote.values
        #                 ]
        #                 self.add_row(*stylized_row, key=quote_key.value)

        #         # Remove extra rows, if any
        #         for r in range(i, len(self.rows)):
        #             self.remove_row(row_key=str(r))

        #         current_row: int = self._state.cursor_row
        #         if current_row >= 0:
        #             if self.cursor_type == "none":
        #                 self.cursor_type = "row"
        #             self.move_cursor(row=current_row)
        #         else:
        #             self.cursor_type = "none"

        #         self._version = self._state.version

    def _update_column_label(self, column_key: str) -> None:
        """Update the label of a column based on its key.

        Args:
            column_key (str): The key of the column to update.
        """

        label = self._get_styled_column_label(column_key)
        self.columns[ColumnKey(column_key)].label = label
        self._update_count += 1
        self.refresh()

    def _get_styled_column_label(self, column_key: str) -> Text:
        """Generate a styled column title based on the column and the current state.

        If the column key matches the sort column key in the current state, an
        arrow indicating the sort direction is added to the column title. The position
        of the arrow depends on the justification of the column: if the column is
        left-justified, the arrow is added at the end of the title; if the column is
        right-justified, the arrow is added at the beginning of the title.

        Args:
            column_key (str): The key of the  column for which to generate a
                styled title.

        Returns:
            Text: The styled column title.
        """

        if not column_key:
            return Text("")

        column: EnhancedColumn[T] = next(
            col for col in self._enhanced_columns if col.key == column_key
        )
        column_label: str = column.label
        if column.key == self._sort_column_key:
            if column.justification == Justify.LEFT:
                if self._sort_direction == SortDirection.ASCENDING:
                    column_label = column_label[: column.width - 2] + " ▼"
                else:
                    column_label = column_label[: column.width - 2] + " ▲"
            else:  # noqa: PLR5501
                if self._sort_direction == SortDirection.ASCENDING:
                    column_label = "▼ " + column_label[: column.width - 2]
                else:
                    column_label = "▲ " + column_label[: column.width - 2]

        return Text(column_label, justify=column.justification.value)

    # Overrides

    @override
    def clear(self, columns: bool = False) -> Self:
        if columns:
            self._enhanced_columns.clear()

        return super().clear(columns)

    @override
    def watch_hover_coordinate(self, old: Coordinate, value: Coordinate) -> None:
        if self.is_ordering:
            return

        if value.row == -1:
            self._hovered_column = value.column
        else:
            self._hovered_column = -1

        super().watch_hover_coordinate(old, value)

    @override
    def watch_cursor_coordinate(
        self, old_coordinate: Coordinate, new_coordinate: Coordinate
    ) -> None:

        super().watch_cursor_coordinate(old_coordinate, new_coordinate)
        self._cursor_row = new_coordinate.row

    @override
    async def _on_click(self, event: events.Click) -> None:
        # Prevent mouse interaction when in ordering (KB-only) mode
        if self.is_ordering:
            event.prevent_default()

    @override
    def _on_mouse_move(self, event: events.MouseMove) -> None:
        # Prevent mouse interaction when in ordering (KB-only) mode
        if self.is_ordering:
            event.prevent_default()

    @override
    def _render_cell(
        self,
        row_index: int,
        column_index: int,
        base_style: Style,
        width: int,
        cursor: bool = False,
        hover: bool = False,
    ) -> SegmentLines:
        current_show_hover_cursor: bool = self._show_hover_cursor
        if row_index == -1:
            if self.is_ordering:
                self._show_hover_cursor = True
            hover = self._hovered_column == column_index  # Mouse mode

        try:
            return super()._render_cell(
                row_index, column_index, base_style, width, cursor, hover
            )
        finally:
            if row_index == -1 and self.is_ordering:
                self._show_hover_cursor = current_show_hover_cursor

    # public API

    def add_enhanced_column(
        self,
        column: EnhancedColumn[T],
    ) -> None:
        """Add an enhanced column to the table.

        Args:
            column (EnhancedColumn): The column to add.
        """
        self._enhanced_columns.append(column)
        super().add_column(
            self._get_styled_column_label(column.key),
            width=column.width,
            key=column.key,
        )

    def add_row_data(self, key: str, row_data: T) -> None:
        """Add an enhanced row to the table.

        Args:
            key (str): The key of the row.
            row_data (T): The data of the row to add.

        Raises:
            RuntimeError: If any column does not have a cell factory defined.
        """

        cells: list[EnhancedTableCell] = []
        for column in self._enhanced_columns:
            cell_factory = column.cell_factory
            if cell_factory is None:
                error_message = f"No cell factory defined for column '{column.key}'."
                raise RuntimeError(error_message)
            cells.append(cell_factory(row_data))

        super().add_row(*cells, key=key)

    def update_row_data(self, key: str, row_data: T) -> None:
        """Update an enhanced row in the table.

        Args:
            key (str): The key of the row.
            row_data (T): The data of the row to update.

        Raises:
            RuntimeError: If any column does not have a cell factory defined.
        """

        for column in self._enhanced_columns:
            cell_factory = column.cell_factory
            if cell_factory is None:
                error_message = f"No cell factory defined for column '{column.key}'."
                raise RuntimeError(error_message)
            self.update_cell(
                key,
                column.key,
                cell_factory(row_data),
            )

    def add_or_update_row_data(self, key: str, row_data: T) -> None:
        """Add or update an enhanced row in the table.

        Args:
            key (str): The key of the row.
            row_data (T): The data of the row to add or update.
        """

        if key in self.rows:
            self.update_row_data(key, row_data)
        else:
            self.add_row_data(key, row_data)

    def remove_row_data(self, key: str) -> None:
        """Remove an enhanced row from the table.

        Args:
            key (str): The key of the row to remove.
        """

        self.remove_row(key)

    @property
    def is_ordering(self) -> bool:
        """Whether the table is in ordering mode."""

        return self._is_ordering

    @is_ordering.setter
    def is_ordering(self, value: bool) -> None:
        if value == self._is_ordering:
            return

        self._set_hover_cursor(active=not value)
        if value:
            if self._hovered_column == -1:
                self._hovered_column = self._sort_column_idx
            self._bindings = self._ordering_bindings
        else:
            self._hovered_column = -1
            self._bindings = self._default_bindings
        self._is_ordering = value

    @property
    def sort_column_key(self) -> str:
        """The key of the column currently used for sorting.

        Raises:
            ValueError: If the provided key is not a valid column key.
        """  # noqa: DOC502

        return self._sort_column_key

    @sort_column_key.setter
    def sort_column_key(self, value: str) -> None:

        if value not in [column.key for column in self._enhanced_columns]:
            error_text = f"Invalid sort column key: {value}"
            raise ValueError(error_text)
        if value != self._sort_column_key:
            prev_key = self._sort_column_key
            self._sort_column_key = value
            if prev_key:
                self._update_column_label(prev_key)
            self._update_column_label(self._sort_column_key)

    @property
    def sort_direction(self) -> SortDirection:
        """The current sort direction."""

        return self._sort_direction

    @sort_direction.setter
    def sort_direction(self, value: SortDirection) -> None:
        if value != self._sort_direction:
            self._sort_direction = value
            self._update_column_label(self._sort_column_key)

    # Keyboard actions for ordering mode

    def action_order_move_right(self) -> None:
        """Move the cursor right in order mode."""

        if self._hovered_column < len(self.columns) - 1:
            self._hovered_column += 1

    def action_order_move_left(self) -> None:
        """Move the cursor left in order mode."""

        # We need the check here cause hovered_column can go to -1 (which signifies
        # the hovered column is inactive)
        # TODO Maybe we should just use a different variable for the hovered state
        # on/off
        if self._hovered_column > 0:
            self._hovered_column -= 1

    def action_order_select(self) -> None:
        """Handle the selecting of the current column in order mode."""

        self._select_column(self._hovered_column)

    # Event handlers

    def on_data_table_header_selected(self, evt: DataTable.HeaderSelected) -> None:
        """Event handler called when the header is clicked.

        Args:
            evt (DataTable.HeaderSelected): The event object.
        """

        self._select_column(evt.column_index)

    # Watchers

    def watch__hovered_column(self, _old: int, _value: int) -> None:
        """Watcher for the hovered column."""

        # Force a re-render of the header row
        self._update_count += 1

    # Helpers

    @property
    def _sort_column_idx(self) -> int:
        """Helper to get the index of the current sort column."""

        try:
            # return the index of the current sort column. It's found by its key
            return self._enhanced_columns.index(
                next(
                    col
                    for col in self._enhanced_columns
                    if col.key == self._sort_column_key
                )
            )
        except ValueError:
            return 0

    def _select_column(self, index: int) -> None:
        """Select the column at the given index.

        Args:
            index (int): The index of the column to select.
        """

        if index != self._sort_column_idx:
            self.sort_column_key = self._enhanced_columns[index].key
        else:
            self.sort_direction = (
                SortDirection.ASCENDING
                if self.sort_direction == SortDirection.DESCENDING
                else SortDirection.DESCENDING
            )

        self.post_message(
            TableSortingChanged(self.sort_column_key, self.sort_direction)
        )
