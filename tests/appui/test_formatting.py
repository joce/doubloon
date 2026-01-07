"""Validate behavior of text formatting utilities for numerical data presentation."""

# pyright: reportPrivateUsage=none

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from appui import formatting as fmt
from calahan.enums import QuoteType


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


@pytest.mark.parametrize(
    ("input_value", "fmt_override", "expected_output"),
    [
        pytest.param(None, None, fmt._NO_VALUE, id="none"),
        pytest.param(date(2024, 1, 2), None, "2024-01-02", id="default"),
        pytest.param(date(2024, 1, 2), "%m/%d/%Y", "01/02/2024", id="override"),
    ],
)
def test_as_date(
    input_value: date | None, fmt_override: str | None, expected_output: str
) -> None:
    """Verify date formatting with default and custom format strings."""

    assert fmt.as_date(input_value, fmt_override) == expected_output


@pytest.mark.parametrize(
    ("input_value", "fmt_override", "expected_output"),
    [
        pytest.param(None, None, fmt._NO_VALUE, id="none"),
        pytest.param(
            datetime(2024, 1, 2, 3, 4, tzinfo=timezone.utc),
            None,
            "2024-01-02 03:04",
            id="default",
        ),
        pytest.param(
            datetime(2024, 1, 2, 3, 4, tzinfo=timezone.utc),
            "%Y/%m/%d %H:%M",
            "2024/01/02 03:04",
            id="override",
        ),
    ],
)
def test_as_datetime(
    input_value: datetime | None, fmt_override: str | None, expected_output: str
) -> None:
    """Verify datetime formatting with default and custom format strings."""

    assert fmt.as_datetime(input_value, fmt_override) == expected_output


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        pytest.param(None, fmt._NO_VALUE, id="none"),
        pytest.param(QuoteType.PRIVATE_COMPANY, "Private Company", id="underscore"),
        pytest.param(QuoteType.ETF, "Etf", id="abbrev"),
    ],
)
def test_as_enum(input_value: QuoteType | None, expected_output: str) -> None:
    """Verify enum formatting into title-cased labels."""

    assert fmt.as_enum(input_value) == expected_output


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        pytest.param(
            "multiple___underscores",
            "Multiple Underscores",
            id="multiple-underscores",
        ),
        pytest.param(
            "__leading_trailing__",
            "Leading Trailing",
            id="leading-trailing-underscores",
        ),
        pytest.param(
            "Already Title Cased",
            "Already Title Cased",
            id="already-title-cased",
        ),
        pytest.param(
            "already_title_cased",
            "Already Title Cased",
            id="underscore-title-cased",
        ),
        pytest.param(
            "mixed__CAPS__and__case",
            "Mixed Caps And Case",
            id="mixed-case",
        ),
    ],
)
def test_as_title_case(input_value: str, expected_output: str) -> None:
    """Verify title casing collapses underscores and normalizes capitalization."""

    assert fmt._as_title_case(input_value) == expected_output


@pytest.mark.parametrize(
    ("input_value", "expected_output"),
    [
        pytest.param(None, fmt._NO_VALUE, id="none"),
        pytest.param(True, "☑", id="checked"),
        pytest.param(False, "☐", id="unchecked"),
    ],
)
def test_as_bool(
    input_value: bool | None,  # noqa: FBT001
    expected_output: str,
) -> None:
    """Verify boolean formatting into checkbox glyphs."""

    assert fmt.as_bool(value=input_value) == expected_output
