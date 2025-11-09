"""Various enums used throughout the application."""

from __future__ import annotations

import logging
from enum import Enum, IntEnum
from typing import TypeVar


class Justify(Enum):
    """Justify enum for the Label class."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class SortDirection(Enum):
    """SortDirection enum for the QuoteTableState class."""

    ASCENDING = "asc"
    DESCENDING = "desc"


class TimeFormat(Enum):
    """TimeFormat enum for time display format."""

    TWELVE_HOUR = "12h"
    TWENTY_FOUR_HOUR = "24h"


class LoggingLevel(IntEnum):
    """Logging levels supported by the Doubloon application."""

    NOTSET = logging.NOTSET
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


T = TypeVar("T", bound=Enum)


def coerce_enum_member(
    enum_type: type[T], value: T | str | float | None, *, strict: bool = False
) -> T | None:
    """Attempt to resolve ``value`` to a member of ``enum_type``.

    Args:
        enum_type (type[T]): The enum class to coerce into.
        value (T | str | float | None): The incoming value that may represent an enum
            member.
        strict (bool): When ``True`` raise ``ValueError`` instead of returning ``None``.

    Returns:
        The matching enum member, or ``None`` if no match can be deduced and
        ``strict`` is ``False``.

    Raises:
        ValueError: If ``strict`` is ``True`` and no matching enum member is found
    """

    if isinstance(value, enum_type):
        return value

    member: T | None = None

    if isinstance(value, str):
        lowered = value.strip().lower()
        for enum_member in enum_type:
            member_value = enum_member.value
            if isinstance(member_value, str) and member_value.lower() == lowered:
                member = enum_member
                break
            if enum_member.name.lower() == lowered:
                member = enum_member
                break
    else:
        for enum_member in enum_type:
            if enum_member.value == value:
                member = enum_member
                break

    if member is not None:
        return member

    if strict:
        error_msg = f"Value '{value}' is not a valid member of {enum_type.__name__}"
        raise ValueError(error_msg)
    return None
