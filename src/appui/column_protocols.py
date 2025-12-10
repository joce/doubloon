"""Protocols for column chooser."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


@runtime_checkable
class ColumnMetadata(Protocol):
    """Minimal column properties for UI display."""

    @property
    def key(self) -> str:
        """Unique identifier for the column."""
        ...

    @property
    def label(self) -> str:
        """Display label for the column."""
        ...


@runtime_checkable
class ColumnContainer(Protocol):
    """A container for active columns with mutation operations."""

    def get_active_keys(self) -> Sequence[str]:
        """Get ordered list of currently active column keys."""
        ...

    def get_frozen_keys(self) -> Sequence[str]:
        """Get list of column keys that cannot be removed (empty if none)."""
        ...

    def add_column(self, key: str) -> None:
        """Add a column to the active list and update display.

        Args:
            key: The column key to add
        """
        ...

    def remove_column(self, key: str) -> None:
        """Remove a column from the active list and update display.

        Args:
            key: The column key to remove

        Raises:
            ValueError: If column is frozen or not in active list
        """
        ...


@runtime_checkable
class ColumnRegistry(Protocol):
    """Read-only access to all available columns.

    Compatible with dict[str, ColumnMetadata] via structural typing.
    """

    def __getitem__(self, key: str, /) -> ColumnMetadata:
        """Get column metadata by key.

        Args:
            key: The column key to look up

        Raises:
            KeyError: If column doesn't exist
        """
        ...

    def keys(self) -> Iterable[str]:
        """Get all available column keys in order."""
        ...
