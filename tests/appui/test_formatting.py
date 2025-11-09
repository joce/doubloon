"""Validate behavior of text formatting utilities for numerical data presentation."""

from __future__ import annotations

import pytest

from appui import formatting as fmt

# pyright: reportPrivateUsage=none


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        pytest.param(None, fmt._NO_VALUE, id="none"),
        pytest.param(0, "0.00%", id="zero"),
        pytest.param(100, "100.00%", id="hundred"),
        pytest.param(12.34, "12.34%", id="positive"),
        pytest.param(12.34444, "12.34%", id="positive-rounded"),
        pytest.param(12.34555, "12.35%", id="positive-rounded-up"),
        pytest.param(-20, "-20.00%", id="negative"),
        pytest.param(-892.76324765, "-892.76%", id="negative-rounded"),
    ],
)
def test_as_percent(input_value: float, expected_output: str) -> None:
    """Verify formatting of numbers into percentage strings."""

    assert fmt.as_percent(input_value) == expected_output


@pytest.mark.parametrize(
    ("input_value", "precision", "expected_output"),
    [
        pytest.param(None, None, fmt._NO_VALUE, id="none-default"),
        pytest.param(1234.5678, None, "1234.57", id="value-default"),
        pytest.param(1234.5678, 3, "1234.568", id="value-precision-3"),
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
        pytest.param(None, fmt._NO_VALUE, id="none"),
        pytest.param(1, "1", id="ones"),
        pytest.param(10, "10", id="tens"),
        pytest.param(200, "200", id="hundreds"),
        pytest.param(1234, "1.23K", id="thousands"),
        pytest.param(1000000, "1.00M", id="millions"),
        pytest.param(1000000000, "1.00B", id="billions"),
        pytest.param(1000000000000, "1.00T", id="trillions"),
    ],
)
def test_as_compact_int(input_value: int, expected_output: str) -> None:
    """Verify compact integer formatting with magnitude-based suffixes (K, M, B, T)."""

    assert fmt.as_compact(input_value) == expected_output
    assert fmt.as_compact(input_value) == expected_output
