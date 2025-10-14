"""Validate The behavior of the `YFinance` class."""

# pylint: disable=broad-exception-caught
# pylint: disable=protected-access

# pyright: reportPrivateUsage=none

import pytest

from calahan import YFinance, YQuote


async def test_yfinance_connects() -> None:
    """Test that the `YFinance` class connects to the Yahoo! Finance API."""

    try:
        yf = YFinance()
        await yf.prime()
    except Exception:  # noqa: BLE001 # any exception is fatal
        pytest.fail("Failed to connect to Yahoo! Finance API")

    assert yf._yclient._crumb

    symbols: list[str] = ["AAPL", "GOOG", "F"]
    quotes: list[YQuote] = await yf.retrieve_quotes(symbols)
    assert len(quotes) == len(symbols)

    for q in quotes:
        assert q.symbol in symbols
        symbols.remove(q.symbol)
