"""Screen for choosing which columns to display."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, ClassVar

from textual import on
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, Static

from .footer import Footer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from textual.app import ComposeResult
    from textual.events import DescendantBlur, DescendantFocus, Mount

    from .column_protocols import ColumnContainer, ColumnRegistry
    from .doubloon_app import DoubloonApp
    from .doubloon_config import DoubloonConfig

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class ColumnChooserScreen(Screen[None]):
    """Dialog screen presenting available and active column lists."""

    app: DoubloonApp

    _MOVE_BINDING_GROUP = Binding.Group("Move")
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "close", "Close", key_display="esc", show=True),
        Binding("space", "toggle_column", "Add/Remove", show=True),
        Binding(
            "alt+up", "move_active_up", "Move Up", show=True, group=_MOVE_BINDING_GROUP
        ),
        Binding(
            "alt+down",
            "move_active_down",
            "Move Down",
            show=True,
            group=_MOVE_BINDING_GROUP,
        ),
    ]

    def __init__(
        self,
        registry: ColumnRegistry,
        container: ColumnContainer,
    ) -> None:
        """Initialize the column chooser dialog.

        Args:
            registry: Provides access to all available columns
            container: Manages the active column list
        """
        super().__init__()
        self._registry: ColumnRegistry = registry
        self._container: ColumnContainer = container

        # Setup bindings and footer
        self._doubloon_config: DoubloonConfig = self.app.config
        self._footer = Footer(self._doubloon_config.time_format)

        # Build frozen column labels
        self._frozen_keys: Sequence[str] = self._container.get_frozen_keys()
        self._frozen_labels: list[Label] = []
        for frozen_key in self._frozen_keys:
            frozen_column = self._registry[frozen_key]
            frozen_label = Label(
                frozen_column.label,
                classes="frozen-column-label",
            )
            frozen_label.tooltip = frozen_column.full_name
            self._frozen_labels.append(frozen_label)
        self._all_keys = list(self._registry.keys())

        self._available_list = ListView(classes="column-list available-list")
        self._active_list = ListView(classes="column-list active-list")

    @override
    def _on_mount(self, event: Mount) -> None:
        super()._on_mount(event)
        self.call_after_refresh(self._populate_lists)

    @override
    def compose(self) -> ComposeResult:
        content = Horizontal(classes="column-chooser-content")
        content.border_title = "\\[ Choose Columns ]"

        with (
            Static(classes="column-chooser-root"),
            content,
        ):
            with Vertical(classes="column-pane"):
                yield Label("Available Columns", classes="pane-title")
                yield self._available_list
            with Vertical(classes="column-pane"):
                yield Label("Active Columns", classes="pane-title")
                yield from self._frozen_labels
                yield self._active_list
        yield self._footer

    @override
    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "move_active_up":
            if self._active_list.has_focus:
                return True if self._can_move_active(-1) else None
            return False
        if action == "move_active_down":
            if self._active_list.has_focus:
                return True if self._can_move_active(1) else None
            return False
        return super().check_action(action, parameters)

    def action_close(self) -> None:
        """Dismiss the screen without making changes."""

        self.dismiss(None)

    async def action_toggle_column(self) -> None:
        """Toggle the selected column between available and active lists."""

        # Determine which list has focus
        if self.focused == self._available_list:
            source_list = self._available_list
            dest_list = self._active_list
            is_adding = True
        elif self.focused == self._active_list:
            source_list = self._active_list
            dest_list = self._available_list
            is_adding = False
        else:
            # Neither list has focus, do nothing
            return

        # Get the selected item
        if source_list.index is None:
            # No selection, do nothing
            return

        selected_item = list(source_list.children)[source_list.index]
        column_key = str(selected_item.id)

        # Save current index for later restoration
        current_index = source_list.index

        # Update via container protocol
        if is_adding:
            self._container.add_column(column_key)
        else:
            # UI-level check: prevent removing frozen columns
            if column_key in self._frozen_keys:
                return  # Silently ignore attempt to remove frozen column
            self._container.remove_column(column_key)

        # Remove item from source list
        await selected_item.remove()

        # Add item to destination list at appropriate position
        if is_adding:
            # Active list: append to end
            dest_list.append(self._build_list_item(column_key))
        else:
            # Available list: insert at position based on registry order
            active_keys = list(self._container.get_active_keys())

            insert_index = [
                key
                for key in self._all_keys
                if key not in active_keys and key not in self._frozen_keys
            ].index(column_key)
            dest_list.insert(insert_index, [self._build_list_item(column_key)])

        new_index = source_list.validate_index(current_index)
        source_list.index = None  # Reset selection to force reactive update
        source_list.index = new_index

        # If we just added a first item to an empty list, set index to 0
        if len(dest_list) == 1:
            dest_list.index = 0

        # Persist configuration
        self.app.persist_config()

    def action_move_active_up(self) -> None:
        """Move the selected active column up by one position.

        This reorders the active list and persists the configuration.
        """

        self._move_active_item(-1)

    def action_move_active_down(self) -> None:
        """Move the selected active column down by one position.

        This reorders the active list and persists the configuration.
        """

        self._move_active_item(1)

    @on(Click, "ListView ListItem")
    async def _on_list_view_clicked(self, event: Click) -> None:
        if event.chain == 2:  # noqa: PLR2004
            await self.action_toggle_column()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Refresh bindings when the active list selection changes.

        This keeps the footer state in sync with reorder availability.

        Args:
            event: The highlight event.
        """

        if event.list_view == self._active_list:
            self.refresh_bindings()

    def _on_descendant_focus(self, event: DescendantFocus) -> None:
        """Handle a descendant widget gaining focus.

        Required for special handling of frozen labels.

        Args:
            event: The focus event.
        """

        if event.widget == self._active_list:
            for frozen_label in self._frozen_labels:
                frozen_label.add_class("focused")
            self.refresh_bindings()

    def _on_descendant_blur(self, event: DescendantBlur) -> None:
        """Handle a descendant widget losing focus.

        Required for special handling of frozen labels.

        Args:
            event: The blur event.
        """

        if event.widget == self._active_list:
            for frozen_label in self._frozen_labels:
                frozen_label.remove_class("focused")
            self.refresh_bindings()

    async def _populate_lists(self) -> None:
        """Populate the available and active column lists."""

        # Use ListView's async clear method
        await self._available_list.clear()
        await self._active_list.clear()

        # Get keys from protocols
        active_keys = list(self._container.get_active_keys())

        # Exclude frozen columns from both lists
        active_keys_to_show = [
            key for key in active_keys if key not in self._frozen_keys
        ]
        available_keys = [
            key
            for key in self._all_keys
            if key not in active_keys and key not in self._frozen_keys
        ]

        for column_key in available_keys:
            self._available_list.append(self._build_list_item(column_key))

        for column_key in active_keys_to_show:
            self._active_list.append(self._build_list_item(column_key))

        if len(self._available_list) > 0:
            self._available_list.index = 0

        if len(self._active_list) > 0:
            self._active_list.index = 0

    def _build_list_item(self, column_key: str) -> ListItem:
        """Create a list item widget for the given column key.

        Args:
            column_key: The column key.

        Returns:
            The list item widget.
        """
        column = self._registry[column_key]
        label = Label(column.label)
        label.tooltip = column.full_name
        return ListItem(label, id=column_key)

    def _can_move_active(self, offset: int) -> bool:
        """Check if the active list's selected item can be moved by the given offset.

        Args:
            offset: The offset to move by (negative for up, positive for down).

        Returns:
            True if the move is possible, False otherwise.
        """

        if self.focused != self._active_list:
            return False
        if self._active_list.index is None:
            return False

        new_index = self._active_list.index + offset
        return 0 <= new_index < len(self._active_list)

    def _move_active_item(self, offset: int) -> None:
        """Move the selected active item by the given offset.

        Args:
            offset: The offset to move by (negative for up, positive for down).
        """

        current_index = self._active_list.index
        if current_index is None:
            return

        items = list(self._active_list.children)
        selected_item = items[current_index]
        new_index = current_index + offset
        if not 0 <= new_index < len(items):
            return

        target_item = items[new_index]
        column_key = str(selected_item.id)

        self._container.move_column(column_key, new_index)

        if offset < 0:
            self._active_list.move_child(selected_item, before=target_item)
        else:
            self._active_list.move_child(selected_item, after=target_item)

        self._active_list.index = new_index
        self.app.persist_config()
