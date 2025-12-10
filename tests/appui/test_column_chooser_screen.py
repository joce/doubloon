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

    def __init__(self, key: str, label: str) -> None:
        self._key = key
        self._label = label

    @property
    def key(self) -> str:
        return self._key

    @property
    def label(self) -> str:
        return self._label


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

    registry = _FakeRegistry([_FakeColumn("alpha", "Alpha Column")])
    container = _FakeContainer(active=[])
    app = _ColumnChooserTestApp(registry, container, DoubloonConfig())

    async with app.run_test() as pilot:
        screen = app.screen_under_test
        await screen._populate_lists()
        await pilot.pause()

        item = next(iter(screen._available_list.children))
        assert isinstance(item, ListItem)
        assert str(item.id) == "alpha"
        assert _label_text(item.query_one(Label)) == "Alpha Column"


@pytest.mark.asyncio
async def test_populate_lists_excludes_frozen_and_preserves_order() -> None:
    """Verify available/active lists respect registry order and omit frozen."""

    registry = _FakeRegistry(
        [
            _FakeColumn("frozen", "Frozen"),
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
        assert [_label_text(label) for label in screen._frozen_labels] == ["Frozen"]


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
