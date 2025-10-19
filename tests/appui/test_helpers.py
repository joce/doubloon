"""Validate formatted number comparison helper functionality."""

# pyright: reportPrivateUsage=none

import pytest

from appui._formatting import _NO_VALUE

from .helpers import compare_compact_ints


@pytest.mark.parametrize(
    ("a", "b", "expected_output"),
    [
        ("5", _NO_VALUE, 1),
        (_NO_VALUE, _NO_VALUE, 0),
        (_NO_VALUE, "5", -1),
        ("74", "5", 1),
        ("74", "74", 0),
        ("74", "500", -1),
        ("74", "50.12K", -1),
        ("74", "42.98M", -1),
        ("74", "124.21B", -1),
        ("74", "50.00T", -1),
        ("50.42K", "5", 1),
        ("50.42K", "10.21K", 1),
        ("50.42K", "50.42K", 0),
        ("50.42K", "68.34K", -1),
        ("50.42K", "42.98M", -1),
        ("50.42K", "124.21B", -1),
        ("50.42K", "50.00T", -1),
        ("321.77M", "5", 1),
        ("321.77M", "10.21K", 1),
        ("321.77M", "21.49M", 1),
        ("321.77M", "321.77M", 0),
        ("321.77M", "442.98M", -1),
        ("321.77M", "124.21B", -1),
        ("321.77M", "50.00T", -1),
        ("9.43B", "5", 1),
        ("9.43B", "10.21K", 1),
        ("9.43B", "21.49M", 1),
        ("9.43B", "2.34B", 1),
        ("9.43B", "9.43B", 0),
        ("9.43B", "124.21B", -1),
        ("9.43B", "50.00T", -1),
        ("974.01T", "5", 1),
        ("974.01T", "10.21K", 1),
        ("974.01T", "21.49M", 1),
        ("974.01T", "2.34B", 1),
        ("974.01T", "124.21T", 1),
        ("974.01T", "974.01T", 0),
        ("974.01T", "999.87T", -1),
    ],
)
def test_compare_compact_ints(a: str, b: str, expected_output: int) -> None:
    """Verify the behavior of the compare_compact_ints helper function."""

    assert compare_compact_ints(a, b) == expected_output
