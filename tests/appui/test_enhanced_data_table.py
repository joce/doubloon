"""Tests for EnhancedDataTable."""

# pyright: reportPrivateUsage=none
# pylint: disable=redefined-outer-name
# pylint: disable=missing-param-doc
# pylint: disable=missing-return-doc
# pylint: disable=missing-yield-doc
# pylint: disable=missing-raises-doc
# pylint: disable=useless-param-doc

from __future__ import annotations

import sys
from dataclasses import dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING, ClassVar, SupportsIndex, cast
from unittest.mock import MagicMock, Mock, call, create_autospec

import pytest
from rich.console import Console
from rich.style import Style
from textual._context import active_app
from textual.app import App, ComposeResult
from textual.coordinate import Coordinate
from textual.widgets import DataTable
from textual.widgets._data_table import ColumnKey

from appui.enhanced_data_table import (
    EnhancedColumn,
    EnhancedDataTable,
    EnhancedTableCell,
)
from appui.enums import Justify, SortDirection
from appui.messages import TableSortingChanged
from tests.appui.helpers import get_column_header_midpoint

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from textual._types import SegmentLines
    from textual.binding import BindingType

    from appui.quote_table import QuoteTable

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


@dataclass
class SampleRow:
    """Simple row used throughout the tests."""

    name: str
    value: float
    count: int


def _default_name_cell(row: SampleRow) -> EnhancedTableCell:
    return EnhancedTableCell((row.name,), row.name, Justify.LEFT)


def _default_value_cell(row: SampleRow) -> EnhancedTableCell:
    return EnhancedTableCell((row.value,), f"{row.value:.2f}", Justify.RIGHT)


def _make_columns(
    name_factory: Callable[[SampleRow], EnhancedTableCell] | None = None,
    value_factory: Callable[[SampleRow], EnhancedTableCell] | None = None,
) -> list[EnhancedColumn[SampleRow]]:
    return [
        EnhancedColumn(
            label="Name",
            key="name",
            width=8,
            justification=Justify.LEFT,
            cell_factory=name_factory or _default_name_cell,
        ),
        EnhancedColumn(
            label="Value",
            key="value",
            width=8,
            justification=Justify.RIGHT,
            cell_factory=value_factory or _default_value_cell,
        ),
    ]


@pytest.fixture(autouse=True)
def activate_dummy_app_context() -> Iterator[MagicMock]:
    """Activate a dummy Textual app context for tests needing it."""

    dummy_app = create_autospec("App", console=Console())
    token = active_app.set(dummy_app)
    try:
        yield dummy_app
    finally:
        active_app.reset(token)


@pytest.fixture
def sample_row() -> SampleRow:
    """Provide a sample row for tests."""

    return SampleRow("Tuna Can", 1.55, 12)


@pytest.fixture
def table_with_columns() -> EnhancedDataTable[SampleRow]:
    """EnhancedDataTable pre-populated with sample columns."""

    table: EnhancedDataTable[SampleRow] = EnhancedDataTable()
    for column in _make_columns():
        table.add_enhanced_column(column)
    return table


def test_enhanced_column_defaults_apply(sample_row: SampleRow) -> None:
    """Columns fall back to label-based keys and a default factory."""

    column: EnhancedColumn[SampleRow] = EnhancedColumn(label="Name")

    assert column.key == "Name"
    assert column.cell_factory is not None
    cell = column.cell_factory(sample_row)
    assert isinstance(cell, EnhancedTableCell)
    assert cell.text == str(sample_row)
    assert cell.justification == column.justification


def test_add_enhanced_column_registers_and_sets_label() -> None:
    """Adding a column registers metadata and updates the header label."""

    table: EnhancedDataTable[SampleRow] = EnhancedDataTable()
    column = _make_columns()[0]

    table.add_enhanced_column(column)

    assert table._enhanced_columns == [column]
    assert ColumnKey(column.key) in table.columns
    label = table.columns[ColumnKey(column.key)].label
    assert label.plain == column.label


def test_update_column_label_refreshes_and_applies_style(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refreshing a column header applies the active sort indicator."""

    table = table_with_columns
    table._sort_column_key = "name"
    table._sort_direction = SortDirection.ASCENDING
    table._update_count = 0
    refresh_spy = Mock()
    monkeypatch.setattr(table, "refresh", refresh_spy)

    table._update_column_label("name")

    assert table.columns[ColumnKey("name")].label.plain.endswith("▲")
    assert table._update_count == 1
    refresh_spy.assert_called_once()


@pytest.mark.parametrize(
    ("justification", "direction", "prefix", "suffix"),
    [
        (Justify.LEFT, SortDirection.ASCENDING, "", " ▲"),
        (Justify.LEFT, SortDirection.DESCENDING, "", " ▼"),
        (Justify.RIGHT, SortDirection.ASCENDING, "▲ ", ""),
        (Justify.RIGHT, SortDirection.DESCENDING, "▼ ", ""),
        (Justify.LEFT, None, "", ""),
        (Justify.RIGHT, None, "", ""),
    ],
)
def test_styled_column_label_places_arrows_correctly(
    justification: Justify,
    direction: SortDirection | None,
    prefix: str,
    suffix: str,
) -> None:
    """Styled column labels position arrows based on justification and direction."""

    column = EnhancedColumn[SampleRow](
        label="Name",
        key="name",
        width=8,
        justification=justification,
    )
    table: EnhancedDataTable[SampleRow] = EnhancedDataTable()
    table.add_enhanced_column(column)

    if direction:
        table.sort_column_key = "name"
        table.sort_direction = direction

    label_text = table.columns[ColumnKey("name")].label.plain
    assert label_text.startswith(prefix)
    assert label_text.endswith(suffix)

    expected_core = column.label if not direction else column.label[: column.width - 2]
    core = label_text.removeprefix(prefix).removesuffix(suffix)
    assert core.strip() == expected_core.strip()


def test_get_styled_column_label_handles_sort_indicators(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Styled column labels reflect sorting state and handle blank text."""

    table = table_with_columns

    table.sort_column_key = "name"
    table.sort_direction = SortDirection.ASCENDING
    name_label = table.columns[ColumnKey("name")].label
    assert name_label.plain.endswith("▲")

    table.sort_column_key = "value"
    table.sort_direction = SortDirection.DESCENDING
    value_label = table.columns[ColumnKey("value")].label
    assert value_label.plain.startswith("▼ ")

    empty_column_label = ""
    assert table._get_styled_column_label("").plain == empty_column_label


def test_add_row_data_creates_cells_and_triggers_sort(
    sample_row: SampleRow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Adding a row builds cells from factories and kicks off sorting."""

    name_factory = Mock(return_value=_default_name_cell(sample_row))
    value_factory = Mock(return_value=_default_value_cell(sample_row))
    table: EnhancedDataTable[SampleRow] = EnhancedDataTable()
    for column in _make_columns(name_factory, value_factory):
        table.add_enhanced_column(column)

    sort_spy = Mock()
    monkeypatch.setattr(table, "sort", sort_spy)
    table.sort_column_key = "name"
    sort_spy.reset_mock()

    table.add_row_data("row-1", sample_row)

    name_factory.assert_called_once_with(sample_row)
    value_factory.assert_called_once_with(sample_row)
    sort_spy.assert_called_once_with("name", reverse=True)


def test_add_row_data_without_factory_raises(sample_row: SampleRow) -> None:
    """Adding a row without a factory raises immediately."""

    table: EnhancedDataTable[SampleRow] = EnhancedDataTable()
    column = _make_columns()[0]
    object.__setattr__(column, "cell_factory", None)  # noqa: PLC2801
    table.add_enhanced_column(column)

    with pytest.raises(RuntimeError, match="No cell factory defined"):
        table.add_row_data("row-1", sample_row)


def test_update_row_data_updates_each_column(
    sample_row: SampleRow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Updating a row rewrites each cell and resorts the table."""

    name_factory = Mock(return_value=_default_name_cell(sample_row))
    value_factory = Mock(return_value=_default_value_cell(sample_row))
    table: EnhancedDataTable[SampleRow] = EnhancedDataTable()
    for column in _make_columns(name_factory, value_factory):
        table.add_enhanced_column(column)

    update_spy = Mock()
    monkeypatch.setattr(table, "update_cell", update_spy)
    sort_spy = Mock()
    monkeypatch.setattr(table, "sort", sort_spy)
    table.sort_column_key = "name"
    sort_spy.reset_mock()

    table.update_row_data("row-1", sample_row)

    expected_calls = [
        call("row-1", "name", name_factory.return_value),
        call("row-1", "value", value_factory.return_value),
    ]
    update_spy.assert_has_calls(expected_calls)
    sort_spy.assert_called_once_with("name", reverse=True)


def test_update_row_data_without_factory_raises(
    table_with_columns: EnhancedDataTable[SampleRow],
    sample_row: SampleRow,
) -> None:
    """Updating a row without a factory produces an error."""

    column = table_with_columns._enhanced_columns[0]
    object.__setattr__(column, "cell_factory", None)  # noqa: PLC2801

    with pytest.raises(RuntimeError, match="No cell factory defined"):
        table_with_columns.update_row_data("row-1", sample_row)


def test_add_or_update_row_data_adds_when_missing(
    table_with_columns: EnhancedDataTable[SampleRow],
    sample_row: SampleRow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Row updates insert new entries when none exist."""

    table = table_with_columns
    monkeypatch.setattr(table, "sort", Mock())
    update_spy = Mock()
    add_spy = Mock()
    monkeypatch.setattr(table, "update_row_data", update_spy)
    monkeypatch.setattr(table, "add_row_data", add_spy)

    table.add_or_update_row_data("row-1", sample_row)

    update_spy.assert_not_called()
    add_spy.assert_called_once_with("row-1", sample_row)


def test_add_or_update_row_data_updates_when_present(
    table_with_columns: EnhancedDataTable[SampleRow],
    sample_row: SampleRow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Row updates overwrite existing entries when already present."""

    table = table_with_columns
    monkeypatch.setattr(table, "sort", Mock())
    table.add_row_data("row-1", sample_row)

    update_spy = Mock()
    add_spy = Mock()
    monkeypatch.setattr(table, "update_row_data", update_spy)
    monkeypatch.setattr(table, "add_row_data", add_spy)

    table.add_or_update_row_data("row-1", sample_row)

    update_spy.assert_called_once_with("row-1", sample_row)
    add_spy.assert_not_called()


def test_remove_row_data_delegates_to_datatable(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Removing a row delegates to the underlying widget."""

    table = table_with_columns
    remove_spy = Mock()
    monkeypatch.setattr(table, "remove_row", remove_spy)

    table.remove_row_data("row-1")

    remove_spy.assert_called_once_with("row-1")


def test_sort_column_key_validation(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Sorting with an unknown key is rejected."""

    table = table_with_columns

    with pytest.raises(ValueError, match="Invalid sort column key"):
        table.sort_column_key = "unknown"


def test_sort_column_key_updates_labels_and_sort(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Changing the sort target updates headers and reorders rows."""

    table = table_with_columns
    sort_spy = Mock()
    monkeypatch.setattr(table, "sort", sort_spy)
    expected_call_count = 0

    table.sort_column_key = "name"
    expected_call_count += 1
    assert table.sort_column_key == "name"
    assert table.columns[ColumnKey("name")].label.plain.endswith(" ▲")

    table.sort_column_key = "value"
    expected_call_count += 1
    assert table.columns[ColumnKey("name")].label.plain == "Name"
    assert table.columns[ColumnKey("value")].label.plain.startswith("▲ ")

    assert sort_spy.call_count == expected_call_count


def test_sort_column_key_same_value_only_resorts(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reapplying the same sort target only resorts without relabeling."""

    table = table_with_columns
    table.sort_column_key = "name"
    update_label_spy = Mock()
    update_sort_spy = Mock()
    monkeypatch.setattr(table, "_update_column_label", update_label_spy)
    monkeypatch.setattr(table, "_update_sort", update_sort_spy)

    table.sort_column_key = "name"

    update_label_spy.assert_not_called()
    update_sort_spy.assert_called_once()


def test_sort_direction_updates_label_and_triggers_sort(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Changing sort direction updates header arrows and resorts."""

    table = table_with_columns
    sort_spy = Mock()
    monkeypatch.setattr(table, "sort", sort_spy)
    table.sort_column_key = "name"
    sort_spy.reset_mock()

    table.sort_direction = SortDirection.DESCENDING

    label = table.columns[ColumnKey("name")].label
    assert label.plain.endswith(" ▼")
    sort_spy.assert_called_once_with("name", reverse=False)


def test_update_sort_respects_direction(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sort updates flip the reverse flag according to direction."""

    table = table_with_columns
    sort_spy = Mock()
    monkeypatch.setattr(table, "sort", sort_spy)
    table.sort_column_key = "name"
    sort_spy.reset_mock()

    table._sort_direction = SortDirection.ASCENDING
    table._update_sort()
    sort_spy.assert_called_once_with("name", reverse=True)

    sort_spy.reset_mock()
    table._sort_direction = SortDirection.DESCENDING
    table._update_sort()
    sort_spy.assert_called_once_with("name", reverse=False)


def test_is_ordering_toggles_bindings_and_hover(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ordering mode switches navigation bindings and hover behavior."""

    table = table_with_columns
    monkeypatch.setattr(table, "sort", Mock())
    table.sort_column_key = "name"
    hover_spy = Mock()
    monkeypatch.setattr(table, "_set_hover_cursor", hover_spy)

    table.is_ordering = True

    hover_spy.assert_called_once_with(active=False)
    assert table._hovered_column == table._sort_column_idx
    assert table._bindings is table._ordering_bindings

    table.is_ordering = False

    hover_spy.assert_called_with(active=True)
    assert table._hovered_column == -1
    assert table._bindings is table._default_bindings


def test_is_ordering_no_change_is_noop(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reapplying the current ordering state changes nothing."""

    table = table_with_columns
    hover_spy = Mock()
    monkeypatch.setattr(table, "_set_hover_cursor", hover_spy)

    table.is_ordering = False

    hover_spy.assert_not_called()


def test_is_ordering_preserves_existing_hover(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Entering ordering mode retains the existing hover target."""

    table = table_with_columns
    table.sort_column_key = "name"
    table._hovered_column = 0

    table.is_ordering = True

    assert table._hovered_column == 0
    assert table._bindings is table._ordering_bindings


def test_keyboard_actions_move_hover_within_bounds(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Ordering navigation clamps the hovered column within bounds."""

    table = table_with_columns
    table._hovered_column = 0

    table.action_order_move_left()
    assert table._hovered_column == 0

    table.action_order_move_right()
    assert table._hovered_column == 1

    table.action_order_move_right()
    assert table._hovered_column == 1


def test_action_order_move_left_decrements_positive_hover(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Moving left reduces the hovered column when possible."""

    table = table_with_columns
    table._hovered_column = 1

    table.action_order_move_left()

    assert table._hovered_column == 0


def test_action_order_select_posts_message_when_column_changes(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Selecting a different column emits a sorting message."""

    table = table_with_columns
    monkeypatch.setattr(table, "sort", Mock())
    table.sort_column_key = "name"
    table._hovered_column = 1
    post_spy = Mock()
    monkeypatch.setattr(table, "post_message", post_spy)

    table.action_order_select()

    assert table.sort_column_key == "value"
    post_spy.assert_called_once()
    message = post_spy.call_args.args[0]
    assert isinstance(message, TableSortingChanged)
    assert message.column_key == "value"


def test_selecting_active_column_toggles_sort_direction(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Selecting the active column flips the sort direction."""

    table = table_with_columns
    expected_call_count = 0
    sort_spy = Mock()
    monkeypatch.setattr(table, "sort", sort_spy)
    table.sort_column_key = "name"
    expected_call_count += 1
    post_spy = Mock()
    monkeypatch.setattr(table, "post_message", post_spy)

    table._select_column(0)
    expected_call_count += 1

    assert table.sort_direction == SortDirection.DESCENDING
    post_spy.assert_called_once()
    assert sort_spy.call_count == expected_call_count


def test_on_header_selected_triggers_selection(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Header selection events route to column selection logic."""

    table = table_with_columns
    select_spy = Mock()
    monkeypatch.setattr(table, "_select_column", select_spy)

    event = create_autospec("HeaderSelected", column_index=1)

    table.on_data_table_header_selected(event)

    select_spy.assert_called_once_with(1)


def test_sort_column_idx_returns_zero_on_value_error(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Sort index defaults to zero when column lookup fails."""

    table = table_with_columns
    table.sort_column_key = "name"

    class FailingColumns(list[EnhancedColumn[SampleRow]]):
        @override
        def index(
            self,
            value: EnhancedColumn[SampleRow],
            start: SupportsIndex = 0,
            stop: SupportsIndex = sys.maxsize,
        ) -> int:
            raise ValueError

    table._enhanced_columns = FailingColumns(table._enhanced_columns)

    assert table._sort_column_idx == 0


def test_watch_hover_coordinate_tracks_header_hover(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hover tracking updates header focus only outside ordering mode."""

    table = table_with_columns
    monkeypatch.setattr(table, "sort", Mock())
    table.sort_column_key = "name"
    start = Coordinate(0, 0)

    table.watch_hover_coordinate(start, Coordinate(-1, 1))
    assert table._hovered_column == 1

    table.watch_hover_coordinate(start, Coordinate(0, 0))
    assert table._hovered_column == -1

    table.is_ordering = True
    table._hovered_column = 0
    table.watch_hover_coordinate(start, Coordinate(-1, 1))
    assert table._hovered_column == 0


def test_watch_cursor_coordinate_tracks_row(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Cursor tracking keeps the internal row index in sync."""

    table = table_with_columns
    start = Coordinate(0, 0)
    table._cursor_row = -1

    cursor_row = 3
    cursor_column = 2

    table.watch_cursor_coordinate(start, Coordinate(cursor_row, cursor_column))

    assert table._cursor_row == cursor_row


def test_watch_hovered_column_increments_update_count(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Hover changes increment the update counter."""

    table = table_with_columns
    table._update_count = 0

    table.watch__hovered_column(-1, 0)

    assert table._update_count == 1


def test_clear_with_columns_resets_enhanced_columns(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Clearing with column removal wipes enhanced metadata."""

    table = table_with_columns

    table.clear(columns=True)

    assert table._enhanced_columns == []


def test_render_cell_header_restores_hover_cursor(
    table_with_columns: EnhancedDataTable[SampleRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Header rendering temporarily adjusts hover cues then restores state."""

    def fake_render_cell(
        _: DataTable[SampleRow],
        __: int,
        ___: int,
        ____: Style,
        _____: int,
        ______: bool,  # noqa: FBT001
        _______: bool,  # noqa: FBT001
    ) -> SegmentLines:
        return cast("SegmentLines", "ok")

    table = table_with_columns
    monkeypatch.setattr(table, "sort", Mock())
    table.sort_column_key = "name"
    table.is_ordering = True
    table._hovered_column = 0
    table._show_hover_cursor = False
    monkeypatch.setattr(DataTable, "_render_cell", fake_render_cell)

    result = table._render_cell(-1, 0, Style(), width=8)

    assert table._show_hover_cursor is False
    assert result == "ok"


@pytest.mark.asyncio
async def test_on_click_prevents_default_when_ordering(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Click handling suppresses events during ordering mode."""

    table = table_with_columns
    table.sort_column_key = "name"
    table.is_ordering = True
    event = create_autospec("Click", prevent_default=Mock())

    await table._on_click(event)

    event.prevent_default.assert_called_once()


def test_on_mouse_move_prevents_default_when_ordering(
    table_with_columns: EnhancedDataTable[SampleRow],
) -> None:
    """Mouse movement suppresses events during ordering mode."""

    table = table_with_columns
    table.sort_column_key = "name"
    table.is_ordering = True
    event = create_autospec("MouseMove", prevent_default=Mock())

    table._on_mouse_move(event)

    event.prevent_default.assert_called_once()


##########################
#  UI / Pilot tests
##########################


@dataclass
class UITestRow:
    """Row used for UI coverage."""

    name: str
    value: float


def _ui_name_cell(row: UITestRow) -> EnhancedTableCell:
    return EnhancedTableCell((row.name,), row.name, justification=Justify.LEFT)


def _ui_value_cell(row: UITestRow) -> EnhancedTableCell:
    return EnhancedTableCell(
        (row.value,),
        f"{row.value:.2f}",
        justification=Justify.RIGHT,
    )


class EnhancedTableUITestApp(App[None]):
    """Minimal Textual app embedding EnhancedDataTable."""

    BINDINGS: ClassVar[list[BindingType]] = [
        ("o", "toggle_ordering", "Toggle Ordering")
    ]

    def __init__(self) -> None:
        """Initialize the test app with an EnhancedDataTable."""

        super().__init__()
        self.table: EnhancedDataTable[UITestRow] = EnhancedDataTable()
        self.table.id = "enhanced-table"
        self._sort_messages: list[TableSortingChanged] = []

    @property
    def sort_messages(self) -> list[TableSortingChanged]:
        """Get collected TableSortingChanged messages."""

        return self._sort_messages

    @override
    def compose(self) -> ComposeResult:
        yield self.table

    def on_mount(self) -> None:
        """Set up the table with columns and data on mount."""

        columns = [
            EnhancedColumn(
                label="Name",
                key="name",
                width=8,
                justification=Justify.LEFT,
                cell_factory=_ui_name_cell,
            ),
            EnhancedColumn(
                label="Value",
                key="value",
                width=8,
                justification=Justify.RIGHT,
                cell_factory=_ui_value_cell,
            ),
        ]
        for column in columns:
            self.table.add_enhanced_column(column)
        self.table.add_row_data("row-1", UITestRow("Cheese", 22.25))
        self.table.add_row_data("row-2", UITestRow("Crackers", 3.07))
        self.table.sort_column_key = "name"
        self.table.sort_direction = SortDirection.ASCENDING
        self.set_focus(self.table)

    def action_toggle_ordering(self) -> None:
        """Toggle column ordering mode."""

        self.table.is_ordering = not self.table.is_ordering

    def on_table_sorting_changed(self, message: TableSortingChanged) -> None:
        """Collect emitted sorting messages for assertions."""

        self._sort_messages.append(message)


@pytest.mark.ui
@pytest.mark.asyncio
async def test_clicking_header_changes_sort_column_and_emits_message() -> None:
    """Header clicks change the sort target and emit notifications."""

    app = EnhancedTableUITestApp()

    async with app.run_test() as pilot:
        table = cast("QuoteTable", app.table)
        assert table.sort_column_key == "name"
        second_column_x = get_column_header_midpoint(table, 1)

        await pilot.click("#enhanced-table", offset=Coordinate(second_column_x, 0))

        assert table.sort_column_key == "value"
        assert table.sort_direction == SortDirection.ASCENDING
        assert app.sort_messages[-1].column_key == "value"
        assert app.sort_messages[-1].direction == SortDirection.ASCENDING


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_mode_uses_keyboard_navigation() -> None:
    """Ordering mode supports keyboard navigation and selection."""

    app = EnhancedTableUITestApp()

    async with app.run_test() as pilot:
        table = app.table

        await pilot.press("o")
        assert table.is_ordering

        await pilot.press("right")
        assert table._hovered_column == 1

        await pilot.press("enter")

        assert table.sort_column_key == "value"
        assert app.sort_messages[-1].column_key == "value"


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_mode_enter_changes_sort_column_when_hovering_new_column() -> (
    None
):
    """In ordering mode, pressing enter on a different column changes sort column."""

    app = EnhancedTableUITestApp()

    async with app.run_test() as pilot:
        table = app.table

        assert table.sort_column_key == "name"
        assert table.sort_direction == SortDirection.ASCENDING

        await pilot.press("o")
        assert table.is_ordering

        await pilot.press("right")
        assert table._hovered_column == 1

        await pilot.press("enter")

        assert table.sort_column_key == "value"
        assert table.sort_direction == SortDirection.ASCENDING
        assert app.sort_messages[-1].column_key == "value"
        assert app.sort_messages[-1].direction == SortDirection.ASCENDING


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_mode_enter_toggles_direction_on_same_column() -> None:
    """In ordering mode, pressing enter on current column toggles direction."""

    app = EnhancedTableUITestApp()

    async with app.run_test() as pilot:
        table = app.table

        assert table.sort_column_key == "name"
        assert table.sort_direction == SortDirection.ASCENDING

        await pilot.press("o")
        assert table.is_ordering
        assert table._hovered_column == 0

        await pilot.press("enter")

        assert table.sort_column_key == "name"
        assert table.sort_direction == SortDirection.DESCENDING
        assert app.sort_messages[-1].column_key == "name"
        assert app.sort_messages[-1].direction == SortDirection.DESCENDING


@pytest.mark.ui
@pytest.mark.asyncio
async def test_ordering_mode_ignores_mouse_clicks_on_headers() -> None:
    """Mouse clicks on headers do nothing while ordering mode is active."""

    app = EnhancedTableUITestApp()

    async with app.run_test() as pilot:
        table = cast("QuoteTable", app.table)

        await pilot.press("o")
        starting_key = table.sort_column_key
        starting_direction = table.sort_direction
        starting_messages = len(app.sort_messages)

        second_column_x = get_column_header_midpoint(table, 1)
        await pilot.click("#enhanced-table", offset=Coordinate(second_column_x, 0))

        assert table.sort_column_key == starting_key
        assert table.sort_direction == starting_direction
        assert len(app.sort_messages) == starting_messages
