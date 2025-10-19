"""Validate behavior of text formatting utilities for numerical data presentation."""

from __future__ import annotations

import pytest

from appui import _formatting as fmt

# pyright: reportPrivateUsage=none


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        (None, fmt._NO_VALUE),
        (0, "0.00%"),
        (100, "100.00%"),
        (12.34, "12.34%"),
        (12.34444, "12.34%"),
        (12.34555, "12.35%"),
        (-20, "-20.00%"),
        (-892.76324765, "-892.76%"),
    ],
)
def test_as_percent(input_value: float, expected_output: str) -> None:
    """Verify formatting of numbers into percentage strings."""

    assert fmt.as_percent(input_value) == expected_output


@pytest.mark.parametrize(
    ("input_value", "precision", "expected_output"),
    [
        (None, None, fmt._NO_VALUE),
        (1234.5678, None, "1234.57"),
        (1234.5678, 3, "1234.568"),
    ],
)
def test_as_float(
    input_value: float | None, precision: int | None, expected_output: str
) -> None:
    """Verify float formatting with default and custom precision specifications."""

    if precision is None:
        assert fmt.as_float(input_value) == expected_output
    else:
        assert fmt.as_float(input_value, precision) == expected_output


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        (None, fmt._NO_VALUE),
        (1, "1"),
        (10, "10"),
        (200, "200"),
        (1234, "1.23K"),
        (1000000, "1.00M"),
        (1000000000, "1.00B"),
        (1000000000000, "1.00T"),
    ],
)
def test_as_compact_int(input_value: int, expected_output: str) -> None:
    """Verify compact integer formatting with magnitude-based suffixes (K, M, B, T)."""

    assert fmt.as_compact(input_value) == expected_output
    assert fmt.as_compact(input_value) == expected_output
