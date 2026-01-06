"""Functions for formatting various data types into strings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from datetime import date, datetime
    from enum import Enum

_NO_VALUE: Final[str] = "N/A"
_DEFAULT_DATE_FORMAT: Final[str] = "%Y-%m-%d"
_DEFAULT_DATETIME_FORMAT: Final[str] = "%Y-%m-%d %H:%M"
_CHECKED_VALUE: Final[str] = "☑"
_UNCHECKED_VALUE: Final[str] = "☐"

# TODO: Allow user-configurable date/time formats via the app configuration.


def _as_title_case(value: str) -> str:
    """Return a title-cased string with underscores treated as word separators.

    Args:
        value (str): The string to normalize.

    Returns:
        str: The normalized, title-cased label.
    """

    return " ".join(word.capitalize() for word in value.replace("_", " ").split())


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


def as_date(value: date | None, fmt: str | None = None) -> str:
    """Return the value formatted as a date string.

    Args:
        value (date | None): The date value to format.
        fmt (str | None): Optional format string to override the default.

    Returns:
        str: The formatted date string or a placeholder if the value is None.
    """

    if value is None:
        return _NO_VALUE
    return value.strftime(fmt or _DEFAULT_DATE_FORMAT)


def as_datetime(value: datetime | None, fmt: str | None = None) -> str:
    """Return the value formatted as a datetime string.

    Args:
        value (datetime | None): The datetime value to format.
        fmt (str | None): Optional format string to override the default.

    Returns:
        str: The formatted datetime string or a placeholder if the value is None.
    """

    if value is None:
        return _NO_VALUE
    return value.strftime(fmt or _DEFAULT_DATETIME_FORMAT)


def as_enum(value: Enum | None) -> str:
    """Return the value formatted as a title-cased enum label.

    Args:
        value (Enum | None): The enumeration value to format.

    Returns:
        str: The formatted enum label or a placeholder if the value is None.
    """

    if value is None:
        return _NO_VALUE
    raw_value = value.value if isinstance(value.value, str) else value.name
    return _as_title_case(str(raw_value))


def as_bool(*, value: bool | None) -> str:
    """Return the value formatted as a checkbox string.

    Args:
        value (bool | None): The boolean value to format.

    Returns:
        str: A checked or unchecked box, or a placeholder if the value is None.
    """

    if value is None:
        return _NO_VALUE
    return _CHECKED_VALUE if value else _UNCHECKED_VALUE
