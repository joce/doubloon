"""Functions for formatting various data types into strings."""

from __future__ import annotations

from typing import Final

_NO_VALUE: Final[str] = "N/A"


def as_percent(value: float | None) -> str:
    """Return the value formatted as a percentage.

    Args:
        value (float | None): The value to be formatted as a percentage.

    Returns:
        str: The percentage representation of the value. If the value is None, returns
            a placeholder string.
    """

    if value is None:
        return _NO_VALUE
    return f"{value:.2f}%"


def as_float(value: float | None, precision: int = 2) -> str:
    """Return the value formatted as a compact float.

    Args:
        value (float | None): The value to be formatted as a float.
        precision (int): The number of decimal places to include in the formatted
            output.

    Returns:
        str: The float representation of the value with the specified precision. If the
            value is None, returns a placeholder string.
    """

    if value is None:
        return _NO_VALUE
    return f"{value:.{precision}f}"


def as_compact(value: int | None) -> str:
    """Return the value formatted as a compact string.

    Large integers are scaled down and suffixed with K, M, B, or T to create a concise,
    human-readable format.

    Args:
        value (int | None): The value to be formatted.

    Returns:
        str: The compact representation of the value. If the value is None, returns a
            placeholder string.

    Examples:
        1500 would be represented as "1.5K".
        45605400 would be represented as "4.56M".
        1000000000 would be represented as "1.00B".
    """

    if value is None:
        return _NO_VALUE
    if value < 1000:  # noqa: PLR2004
        return str(value)
    if value < 1000000:  # noqa: PLR2004
        return f"{value / 1000:.2f}K"
    if value < 1000000000:  # noqa: PLR2004
        return f"{value / 1000000:.2f}M"
    if value < 1000000000000:  # noqa: PLR2004
        return f"{value / 1000000000:.2f}B"

    return f"{value / 1000000000000:.2f}T"
