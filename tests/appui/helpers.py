"""AppUI test helpers."""

# pyright: reportPrivateUsage=none

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from appui.formatting import _NO_VALUE

if TYPE_CHECKING:
    from textual.pilot import Pilot

    from appui.quote_table import QuoteTable


def compare_compact_ints(a: str, b: str) -> int:
    """Compare two compact integers, provided as strings.

    Args:
        a (str): first compact integer
        b (str): second compact integer

    Returns:
        int: -1 if a < b, 1 if a > b, 0 if a == b
    """

    if _NO_VALUE in {a, b}:
        return 0 if a == b else 1 if b == _NO_VALUE else -1

    if a[-1].isdigit():
        if b[-1].isdigit():
            a_int = int(a)
            b_int = int(b)
            return -1 if a_int < b_int else 1 if a_int > b_int else 0
        return -1

    if b[-1].isdigit():
        return 1

    if a[-1] == b[-1]:
        a_flt = float(a[:-1])
        b_flt = float(b[:-1])
        return -1 if a_flt < b_flt else 1 if a_flt > b_flt else 0

    abbrevs: list[str] = ["K", "M", "B", "T"]
    return -1 if abbrevs.index(a[-1]) < abbrevs.index(b[-1]) else 1


def get_column_header_midpoint(table: QuoteTable, column_index: int) -> int:
    """Calculate the x-coordinate of the midpoint of a column header.

    Args:
        table: The EnhancedDataTable instance.
        column_index: The index of the column (0-based).

    Returns:
        The x-coordinate of the column header's midpoint.
    """
    x_offset = 0
    for i, column in enumerate(table._enhanced_columns):
        if i == column_index:
            # Return the midpoint of this column
            return x_offset + (column.width // 2)
        # Add the full width of this column plus separator (1 character)
        x_offset += column.width + 1
    # If we reach here, return the last computed offset
    return x_offset


async def pilot_type_text(pilot: Pilot[Any], text: str) -> None:
    """Type characters into the currently focused widget via Pilot.

    Args:
        pilot: The Pilot instance.
        text: The text to type.
    """

    for char in text:
        key = "space" if char == " " else char
        await pilot.press(key)


async def pilot_clear_text(pilot: Pilot[Any], length: int) -> None:
    """Clear ``length`` characters using backspace events.

    Args:
        pilot: The Pilot instance.
        length: The number of characters to delete.
    """

    for _ in range(length):
        await pilot.press("backspace")


async def pilot_press_repeat(pilot: Pilot[Any], key: str, times: int) -> None:
    """Press ``key`` ``times`` times.

    Args:
        pilot: The Pilot instance.
        key: The key to press.
        times: The number of times to press the key.

    Raises:
        ValueError: If ``times`` is negative.
    """

    if times < 0:
        msg = f"Invalid times value: {times}, must be >= 0"
        raise ValueError(msg)
    keys: list[str] = [key] * times
    if keys:
        await pilot.press(*keys)
