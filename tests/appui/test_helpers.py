"""Validate formatted number comparison helper functionality."""

# pyright: reportPrivateUsage=none

import pytest

from appui.formatting import _NO_VALUE

from .helpers import compare_compact_ints


@pytest.mark.parametrize(
    ("a", "b", "expected_output"),
    [
        pytest.param("5", _NO_VALUE, 1, id="5_gt__NO_VALUE"),
        pytest.param(_NO_VALUE, _NO_VALUE, 0, id="_NO_VALUE_equal__NO_VALUE"),
        pytest.param(_NO_VALUE, "5", -1, id="_NO_VALUE_lt_5"),
        pytest.param("74", "5", 1, id="74_gt_5"),
        pytest.param("74", "74", 0, id="74_equal_74"),
        pytest.param("74", "500", -1, id="74_lt_500"),
        pytest.param("74", "50.12K", -1, id="74_lt_50.12K"),
        pytest.param("74", "42.98M", -1, id="74_lt_42.98M"),
        pytest.param("74", "124.21B", -1, id="74_lt_124.21B"),
        pytest.param("74", "50.00T", -1, id="74_lt_50.00T"),
        pytest.param("50.42K", "5", 1, id="50.42K_gt_5"),
        pytest.param("50.42K", "10.21K", 1, id="50.42K_gt_10.21K"),
        pytest.param("50.42K", "50.42K", 0, id="50.42K_equal_50.42K"),
        pytest.param("50.42K", "68.34K", -1, id="50.42K_lt_68.34K"),
        pytest.param("50.42K", "42.98M", -1, id="50.42K_lt_42.98M"),
        pytest.param("50.42K", "124.21B", -1, id="50.42K_lt_124.21B"),
        pytest.param("50.42K", "50.00T", -1, id="50.42K_lt_50.00T"),
        pytest.param("321.77M", "5", 1, id="321.77M_gt_5"),
        pytest.param("321.77M", "10.21K", 1, id="321.77M_gt_10.21K"),
        pytest.param("321.77M", "21.49M", 1, id="321.77M_gt_21.49M"),
        pytest.param("321.77M", "321.77M", 0, id="321.77M_equal_321.77M"),
        pytest.param("321.77M", "442.98M", -1, id="321.77M_lt_442.98M"),
        pytest.param("321.77M", "124.21B", -1, id="321.77M_lt_124.21B"),
        pytest.param("321.77M", "50.00T", -1, id="321.77M_lt_50.00T"),
        pytest.param("9.43B", "5", 1, id="9.43B_gt_5"),
        pytest.param("9.43B", "10.21K", 1, id="9.43B_gt_10.21K"),
        pytest.param("9.43B", "21.49M", 1, id="9.43B_gt_21.49M"),
        pytest.param("9.43B", "2.34B", 1, id="9.43B_gt_2.34B"),
        pytest.param("9.43B", "9.43B", 0, id="9.43B_equal_9.43B"),
        pytest.param("9.43B", "124.21B", -1, id="9.43B_lt_124.21B"),
        pytest.param("9.43B", "50.00T", -1, id="9.43B_lt_50.00T"),
        pytest.param("974.01T", "5", 1, id="974.01T_gt_5"),
        pytest.param("974.01T", "10.21K", 1, id="974.01T_gt_10.21K"),
        pytest.param("974.01T", "21.49M", 1, id="974.01T_gt_21.49M"),
        pytest.param("974.01T", "2.34B", 1, id="974.01T_gt_2.34B"),
        pytest.param("974.01T", "124.21T", 1, id="974.01T_gt_124.21T"),
        pytest.param("974.01T", "974.01T", 0, id="974.01T_equal_974.01T"),
        pytest.param("974.01T", "999.87T", -1, id="974.01T_lt_999.87T"),
    ],
)
def test_compare_compact_ints(a: str, b: str, expected_output: int) -> None:
    """Verify the behavior of the compare_compact_ints helper function."""

    assert compare_compact_ints(a, b) == expected_output
