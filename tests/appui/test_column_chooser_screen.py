"""Tests for ColumnChooserScreen."""

# pyright: reportPrivateUsage=none
# pylint: disable=missing-return-doc

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from textual.app import App
from textual.widgets import Label, ListItem, ListView

from appui.column_chooser_screen import ColumnChooserScreen
from appui.column_protocols import ColumnContainer, ColumnMetadata, ColumnRegistry
from appui.doubloon_config import DoubloonConfig

if TYPE_CHECKING:
    from collections.abc import Iterable


class _FakeColumn(ColumnMetadata):
    """Minimal column metadata for tests."""

    def __init__(self, key: str, label: str, full_name: str | None = None) -> None:
        self._key = key
        self._label = label
        self._full_name = full_name or label

    @property
    def key(self) -> str:
        return self._key

    @property
    def label(self) -> str:
        return self._label

    @property
    def full_name(self) -> str:
        return self._full_name


class _FakeRegistry(ColumnRegistry):
    """Ordered registry backed by a dict."""

    def __init__(self, columns: Iterable[_FakeColumn]) -> None:
        self._columns = {column.key: column for column in columns}
        self._order = [column.key for column in columns]

    def __getitem__(self, key: str) -> ColumnMetadata:
        return self._columns[key]

    def keys(self) -> Iterable[str]:
        return list(self._order)


class _FakeContainer(ColumnContainer):
    """Mutable container that tracks calls."""

    def __init__(self, active: list[str], frozen: list[str] | None = None) -> None:
        self._active = list(active)
        self._frozen = list(frozen or [])
        self.add_calls: list[str] = []
        self.remove_calls: list[str] = []
        self.move_calls: list[tuple[str, int]] = []

    def get_active_keys(self) -> list[str]:
        return list(self._active)

    def get_frozen_keys(self) -> list[str]:
        return list(self._frozen)

    def add_column(self, key: str) -> None:
        self.add_calls.append(key)
        self._active.append(key)

    def remove_column(self, key: str) -> None:
        self.remove_calls.append(key)
        self._active.remove(key)

    def move_column(self, key: str, new_index: int) -> None:
        self.move_calls.append((key, new_index))
        current_index = self._active.index(key)
        self._active.pop(current_index)
        self._active.insert(new_index, key)


class _ColumnChooserTestApp(App[None]):
    """Harness to mount ColumnChooserScreen with injected state."""

    def __init__(
        self,
        registry: ColumnRegistry,
        container: ColumnContainer,
        config: DoubloonConfig,
    ) -> None:
        super().__init__()
        self.config = config
        self._column_registry = registry
        self._column_container = container
        self.persist_config_mock: MagicMock = MagicMock()
        self._screen: ColumnChooserScreen | None = None

    @property
    def screen_under_test(self) -> ColumnChooserScreen:
        """Lazily construct the screen to ensure app context exists."""

        if self._screen is None:
            self._screen = ColumnChooserScreen(
                self._column_registry, self._column_container
            )
        return self._screen

    def on_mount(self) -> None:
        """Push the column chooser when the app mounts."""

        self.push_screen(self.screen_under_test)

    def persist_config(self) -> None:
        """Record persistence requests."""

        self.persist_config_mock()


def _list_item_ids(list_view: ListView) -> list[str]:
    """Extract list item ids from a ListView.

    Args:
        list_view: The ListView to extract from.

    Returns:
        List of item ids as strings.
    """

    return [str(item.id) for item in list(list_view.children)]


def _label_text(label: Label) -> str:
    """Return the plain text from a Label.

    Args:
        label: The Label widget.

    Returns:
        The plain text of the label.
    """

    return str(label.render())


@pytest.mark.asyncio
async def test_build_list_item_uses_registry_label() -> None:
    """Ensure list items mirror registry labels and keys."""

    registry = _FakeRegistry(
        [_FakeColumn("alpha", "Alpha Column", full_name="Alpha Column Full")]
    )
    container = _FakeContainer(active=[])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()
        await pilot.pause()

        item = next(iter(screen._available_list.children))
        assert isinstance(item, ListItem)
        assert str(item.id) == "alpha"
        label = item.query_one(Label)
        assert _label_text(label) == "Alpha Column"
        assert label.tooltip == "Alpha Column Full"


@pytest.mark.asyncio
async def test_populate_lists_excludes_frozen_and_preserves_order() -> None:
    """Verify available/active lists respect registry order and omit frozen."""

    registry = _FakeRegistry(
        [
            _FakeColumn("frozen", "Frozen", full_name="Frozen Column"),
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
            _FakeColumn("third", "Third"),
        ]
    )
    container = _FakeContainer(active=["frozen", "second"], frozen=["frozen"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test():
        screen = app.screen_under_test
        await screen._populate_lists()

        assert _list_item_ids(screen._available_list) == ["first", "third"]
        assert _list_item_ids(screen._active_list) == ["second"]
        frozen_label = screen._frozen_labels[0]
        assert _label_text(frozen_label) == "Frozen"
        assert frozen_label.tooltip == "Frozen Column"


@pytest.mark.ui
@pytest.mark.asyncio
async def test_toggle_add_moves_item_and_persists() -> None:
    """Adding from available appends to active, adjusts selection, and persists."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
            _FakeColumn("third", "Third"),
        ]
    )
    container = _FakeContainer(active=["first"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._available_list.index = 1
        screen._available_list.focus()

        await pilot.press("space")

        assert container.add_calls == ["third"]
        assert _list_item_ids(screen._active_list) == ["first", "third"]
        assert _list_item_ids(screen._available_list) == ["second"]
        assert screen._available_list.index == 0
        app.persist_config_mock.assert_called_once_with()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_toggle_remove_moves_item_into_registry_order_and_persists() -> None:
    """Removing from active reinserts into available by registry order and persists."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
            _FakeColumn("third", "Third"),
            _FakeColumn("fourth", "Fourth"),
        ]
    )
    container = _FakeContainer(active=["first", "third"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._active_list.index = 1
        screen._active_list.focus()

        await pilot.press("space")

        assert container.remove_calls == ["third"]
        assert _list_item_ids(screen._active_list) == ["first"]
        assert _list_item_ids(screen._available_list) == ["second", "third", "fourth"]
        assert screen._active_list.index == 0
        app.persist_config_mock.assert_called_once_with()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_toggle_last_item_updates_watch_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify toggling the last item keeps the source index at the new tail."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
            _FakeColumn("third", "Third"),
        ]
    )
    container = _FakeContainer(active=[])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._available_list.index = 2
        screen._available_list.focus()

        calls: list[tuple[ListView, int | None, int | None]] = []
        original_watch_index = ListView.watch_index

        def _watch_index(
            self: ListView, old_index: int | None, new_index: int | None
        ) -> None:
            calls.append((self, old_index, new_index))
            original_watch_index(self, old_index, new_index)

        monkeypatch.setattr(ListView, "watch_index", _watch_index)

        await pilot.press("space")

        source_calls = [call for call in calls if call[0] is screen._available_list]
        new_indices = [call[2] for call in source_calls]
        assert new_indices == [None, 1]


@pytest.mark.ui
@pytest.mark.asyncio
async def test_toggle_only_item_updates_watch_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify toggling the final item reports a None index for the source list."""

    registry = _FakeRegistry([_FakeColumn("only", "Only")])
    container = _FakeContainer(active=[])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._available_list.index = 0
        screen._available_list.focus()

        calls: list[tuple[ListView, int | None, int | None]] = []
        original_watch_index = ListView.watch_index

        def _watch_index(
            self: ListView, old_index: int | None, new_index: int | None
        ) -> None:
            calls.append((self, old_index, new_index))
            original_watch_index(self, old_index, new_index)

        monkeypatch.setattr(ListView, "watch_index", _watch_index)

        await pilot.press("space")

        source_calls = [call for call in calls if call[0] is screen._available_list]
        new_indices = [call[2] for call in source_calls]
        assert new_indices == [None]


@pytest.mark.ui
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("active_keys", "focused_list_attr", "dest_list_attr"),
    [
        pytest.param([], "_available_list", "_active_list", id="adding_first_item"),
        pytest.param(
            ["first", "second"],
            "_active_list",
            "_available_list",
            id="removing_first_item",
        ),
    ],
)
async def test_toggle_sets_dest_index_when_first_item_added(
    active_keys: list[str],
    focused_list_attr: str,
    dest_list_attr: str,
) -> None:
    """Ensure adding a first item sets the destination list index to zero."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
        ]
    )
    container = _FakeContainer(active=active_keys)
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        focused_list = getattr(screen, focused_list_attr)
        dest_list = getattr(screen, dest_list_attr)

        if focused_list is screen._available_list:
            screen._active_list.index = None
        else:
            screen._available_list.index = None

        focused_list.index = 0
        focused_list.focus()

        await pilot.press("space")

        assert dest_list.index == 0


@pytest.mark.ui
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "use_available_list",
    [
        pytest.param(True, id="double_click_available_list"),
        pytest.param(False, id="double_click_active_list"),
    ],
)
async def test_double_click_toggles_selected_item(
    use_available_list: bool,  # noqa: FBT001
) -> None:
    """Ensure a double click toggles the selected item for either list."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
            _FakeColumn("third", "Third"),
        ]
    )
    container = _FakeContainer(active=["first", "second"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        if use_available_list:
            screen._available_list.index = 0
            screen._available_list.focus()
        else:
            screen._active_list.index = 0
            screen._active_list.focus()

        event = MagicMock(chain=2)

        await pilot.pause()
        await screen._on_list_view_clicked(event)
        await pilot.pause()

        if use_available_list:
            assert not _list_item_ids(screen._available_list)
            assert _list_item_ids(screen._active_list) == ["first", "second", "third"]
            assert container.add_calls == ["third"]
            assert not container.remove_calls
        else:
            assert _list_item_ids(screen._available_list) == ["first", "third"]
            assert _list_item_ids(screen._active_list) == ["second"]
            assert not container.add_calls
            assert container.remove_calls == ["first"]

        app.persist_config_mock.assert_called_once_with()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_toggle_no_focus_is_noop() -> None:
    """When no list has focus, toggle action should not change state."""

    registry = _FakeRegistry([_FakeColumn("only", "Only")])
    container = _FakeContainer(active=[])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen.focused = None
        await pilot.press("space")

        assert not container.add_calls
        assert not container.remove_calls
        assert _list_item_ids(screen._available_list) == ["only"]
        app.persist_config_mock.assert_not_called()


@pytest.mark.ui
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "use_available_list",
    [
        pytest.param(True, id="use_available_list"),
        pytest.param(False, id="use_active_list"),
    ],
)
async def test_toggle_no_selection_is_noop(
    use_available_list: bool,  # noqa: FBT001
) -> None:
    """Toggle with no highlighted item leaves lists unchanged."""

    registry = _FakeRegistry([_FakeColumn("only", "Only")])
    container = _FakeContainer(active=[])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        if use_available_list:
            screen._available_list.focus()
            screen._available_list.index = None
        else:
            screen._active_list.focus()
            screen._active_list.index = None

        await pilot.press("space")

        assert not container.add_calls
        assert _list_item_ids(screen._available_list) == ["only"]
        app.persist_config_mock.assert_not_called()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_toggle_ignores_frozen_removal_attempt() -> None:
    """Attempting to remove a frozen column is silently ignored."""

    registry = _FakeRegistry(
        [
            _FakeColumn("frozen", "Frozen"),
            _FakeColumn("other", "Other"),
        ]
    )
    container = _FakeContainer(active=["frozen"], frozen=["frozen"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._active_list.append(screen._build_list_item("frozen"))
        screen._active_list.index = 0
        screen._active_list.focus()

        await pilot.press("space")

        assert not container.remove_calls
        assert _list_item_ids(screen._active_list) == ["frozen"]
        assert _list_item_ids(screen._available_list) == ["other"]


@pytest.mark.ui
@pytest.mark.asyncio
async def test_move_active_item_up_reorders_and_persists() -> None:
    """Move active item up, update order/index, and persist config."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
            _FakeColumn("third", "Third"),
        ]
    )
    container = _FakeContainer(active=["first", "second", "third"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._active_list.index = 1
        screen._move_active_item(-1)
        await pilot.pause()

        assert _list_item_ids(screen._active_list) == ["second", "first", "third"]
        assert screen._active_list.index == 0
        assert container.move_calls == [("second", 0)]
        app.persist_config_mock.assert_called_once_with()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_move_active_item_down_reorders_and_persists() -> None:
    """Move active item down, update order/index, and persist config."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
            _FakeColumn("third", "Third"),
        ]
    )
    container = _FakeContainer(active=["first", "second", "third"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._active_list.index = 1
        screen._move_active_item(1)
        await pilot.pause()

        assert _list_item_ids(screen._active_list) == ["first", "third", "second"]
        assert screen._active_list.index == 2  # noqa: PLR2004
        assert container.move_calls == [("second", 2)]
        app.persist_config_mock.assert_called_once_with()


@pytest.mark.ui
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("start_index", "offset"),
    [
        pytest.param(0, -1, id="move_up_from_first"),
        pytest.param(2, 1, id="move_down_from_last"),
    ],
)
async def test_move_active_item_out_of_bounds_is_noop(
    start_index: int, offset: int
) -> None:
    """Out-of-range moves should not reorder or persist."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
            _FakeColumn("third", "Third"),
        ]
    )
    container = _FakeContainer(active=["first", "second", "third"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._active_list.index = start_index
        screen._move_active_item(offset)
        await pilot.pause()

        assert _list_item_ids(screen._active_list) == ["first", "second", "third"]
        assert screen._active_list.index == start_index
        assert not container.move_calls
        app.persist_config_mock.assert_not_called()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_move_active_item_no_selection_is_noop() -> None:
    """No selection should skip moves and persistence."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
        ]
    )
    container = _FakeContainer(active=["first", "second"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._active_list.index = None
        screen._move_active_item(1)
        await pilot.pause()

        assert _list_item_ids(screen._active_list) == ["first", "second"]
        assert screen._active_list.index is None
        assert not container.move_calls
        app.persist_config_mock.assert_not_called()
        app.persist_config_mock.assert_not_called()


@pytest.mark.asyncio
async def test_action_close_dismisses_screen() -> None:
    """Ensure close action dismisses without changes."""

    registry = _FakeRegistry([_FakeColumn("only", "Only")])
    container = _FakeContainer(active=[])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test():
        screen = app.screen_under_test
        screen.dismiss = MagicMock()

        screen.action_close()

        screen.dismiss.assert_called_once_with(None)


@pytest.mark.asyncio
async def test_focus_and_blur_toggle_frozen_label_class() -> None:
    """Frozen labels gain and lose focus styling with active list focus changes."""

    registry = _FakeRegistry([_FakeColumn("frozen", "Frozen")])
    container = _FakeContainer(active=["frozen"], frozen=["frozen"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test():
        screen = app.screen_under_test
        frozen_label = screen._frozen_labels[0]
        blur_event = MagicMock(widget=screen._active_list)
        focus_event = MagicMock(widget=screen._active_list)

        assert not frozen_label.has_class("focused")

        screen._on_descendant_focus(focus_event)
        assert frozen_label.has_class("focused")

        screen._on_descendant_blur(blur_event)
        assert not frozen_label.has_class("focused")


@pytest.mark.ui
@pytest.mark.asyncio
async def test_toggle_with_empty_list_leaves_index_none() -> None:
    """Toggling from an empty list leaves selection index as None."""

    registry = _FakeRegistry([_FakeColumn("only", "Only")])
    container = _FakeContainer(active=[])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        source_list = screen._available_list
        source_list.index = 0

        # Remove the only item to make the list empty
        await pilot.press("space")

        # Verify index is now None
        new_index = source_list.index

        # Empty list, no selection
        assert new_index is None


@pytest.mark.ui
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("key_press", "start_index", "expected_index", "expected_order"),
    [
        pytest.param(
            "alt+up",
            1,
            0,
            ["second", "first", "third"],
            id="move_up",
        ),
        pytest.param(
            "alt+down",
            1,
            2,
            ["first", "third", "second"],
            id="move_down",
        ),
    ],
)
async def test_move_active_reorders_and_persists(
    key_press: str,
    start_index: int,
    expected_index: int,
    expected_order: list[str],
) -> None:
    """Move an active column to update order, selection, and persistence."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
            _FakeColumn("third", "Third"),
        ]
    )
    container = _FakeContainer(active=["first", "second", "third"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._active_list.index = start_index
        screen._active_list.focus()
        await pilot.pause()

        await pilot.press(key_press)

        assert _list_item_ids(screen._active_list) == expected_order
        assert screen._active_list.index == expected_index
        assert container.move_calls == [("second", expected_index)]
        app.persist_config_mock.assert_called_once_with()


@pytest.mark.ui
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("key_press", "start_index"),
    [
        pytest.param("alt+up", 0, id="move_up_at_top"),
        pytest.param("alt+down", 2, id="move_down_at_bottom"),
    ],
)
async def test_move_active_boundary_is_noop(
    key_press: str,
    start_index: int,
) -> None:
    """Attempt to move past boundaries without changing state."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
            _FakeColumn("third", "Third"),
        ]
    )
    container = _FakeContainer(active=["first", "second", "third"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._active_list.index = start_index
        screen._active_list.focus()
        await pilot.pause()

        await pilot.press(key_press)

        assert _list_item_ids(screen._active_list) == ["first", "second", "third"]
        assert screen._active_list.index == start_index
        assert not container.move_calls
        app.persist_config_mock.assert_not_called()


@pytest.mark.ui
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("focus_active", "set_index"),
    [
        pytest.param(False, 0, id="no_focus"),
        pytest.param(True, None, id="no_selection"),
    ],
)
async def test_move_active_disabled_without_focus_or_selection(
    focus_active: bool,  # noqa: FBT001
    set_index: int | None,
) -> None:
    """Disable moves without focus or a selection."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
        ]
    )
    container = _FakeContainer(active=["first", "second"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        if focus_active:
            screen._active_list.focus()
        else:
            screen._available_list.focus()
        screen._active_list.index = set_index
        await pilot.pause()

        await pilot.press("alt+up")

        assert _list_item_ids(screen._active_list) == ["first", "second"]
        assert not container.move_calls
        app.persist_config_mock.assert_not_called()


@pytest.mark.ui
@pytest.mark.asyncio
async def test_move_active_actions_report_disabled_at_edges() -> None:
    """Report disabled state for move actions at list boundaries."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
        ]
    )
    container = _FakeContainer(active=["first", "second"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._active_list.index = 0
        screen._active_list.focus()
        await pilot.pause()
        assert screen.check_action("move_active_up", ()) is None

        screen._active_list.index = 1
        screen._active_list.focus()
        await pilot.pause()
        assert screen.check_action("move_active_down", ()) is None


@pytest.mark.ui
@pytest.mark.asyncio
async def test_move_active_actions_hidden_without_focus() -> None:
    """Hide move actions when the active list does not have focus."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
        ]
    )
    container = _FakeContainer(active=["first", "second"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._available_list.focus()
        await pilot.pause()

        assert screen.check_action("move_active_up", ()) is False
        assert screen.check_action("move_active_down", ()) is False


@pytest.mark.ui
@pytest.mark.asyncio
async def test_move_active_returns_when_index_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return early when the active list index is None."""

    registry = _FakeRegistry(
        [
            _FakeColumn("first", "First"),
            _FakeColumn("second", "Second"),
        ]
    )
    container = _FakeContainer(active=["first", "second"])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test():
        screen = app.screen_under_test
        await screen._populate_lists()

        screen._active_list.index = None

        def _allow_move(_: int) -> bool:
            return True

        monkeypatch.setattr(screen, "_can_move_active", _allow_move)

        screen._move_active_item(-1)

        assert _list_item_ids(screen._active_list) == ["first", "second"]
        assert screen._active_list.index is None
        assert not container.move_calls
        app.persist_config_mock.assert_not_called()
