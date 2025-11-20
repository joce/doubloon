"""Integration tests that hit the live Yahoo! Finance endpoints."""

# pyright: reportPrivateUsage=none

from __future__ import annotations

import pytest

from calahan import YFinance, YQuote, YSearchResult


@pytest.mark.integration
async def test_yfinance_yquote_returns_results() -> None:
    """Connect to Yahoo! Finance quote API and retrieve a small symbol set."""

    try:
        yf = YFinance()
        await yf.prime()
    except Exception:  # noqa: BLE001 # any exception is fatal
        pytest.fail("Failed to connect to Yahoo! Finance Quote API")

    assert yf._yclient._crumb

    symbols: list[str] = ["AAPL", "GOOG", "F"]
    quotes: list[YQuote] = await yf.retrieve_quotes(symbols)
    assert len(quotes) == len(symbols)

    for quote in quotes:
        assert quote.symbol in symbols
        symbols.remove(quote.symbol)


@pytest.mark.integration
async def test_yfinance_yquote_returns_results_exceeding_limits() -> None:
    """Connect to Yahoo! Finance quote API and exercise batching beyond limit."""

    try:
        yf = YFinance()
        await yf.prime()
    except Exception:  # noqa: BLE001 # any exception is fatal
        pytest.fail("Failed to connect to Yahoo! Finance Quote API")

    assert yf._yclient._crumb

    symbols: list[str] = [
        "AAPL",
        "ABNB",
        "ADBE",
        "AMD",
        "AMZN",
        "ARM",
        "AVGO",
        "CSCO",
        "F",
        "GOOG",
        "IBM",
        "INTC",
        "LRCX",
        "MSFT",
        "MU",
        "NFLX",
        "NVDA",
        "ORCL",
        "QCOM",
        "SHOP",
        "TSLA",
        "TXN",
        "UBER",
        "RHM.DE",
        "UBI.PA",
        "GLEN.L",
        "CCO.TO",
    ]
    quotes: list[YQuote] = await yf.retrieve_quotes(symbols)
    assert len(quotes) == len(symbols)

    for quote in quotes:
        assert quote.symbol in symbols
        symbols.remove(quote.symbol)


@pytest.mark.integration
async def test_yfinance_search_returns_results() -> None:
    """Exercise the live search endpoint for a common query."""

    yf = YFinance()
    try:
        await yf.prime()
    except Exception:  # noqa: BLE001
        pytest.fail("Failed to connect to Yahoo! Finance Search API")

    result: YSearchResult | None = None
    try:
        result = await yf.search(
            "mortgage",
            enable_news=True,
            news_count=5,
            enable_lists=True,
            lists_count=2,
            enable_nav_links=True,
        )
    except Exception:  # noqa: BLE001
        pytest.fail("Search request for 'mortgage' failed")
    finally:
        await yf.aclose()

    assert result is not None
    assert result.count > 0
    assert result.quotes or result.news or result.lists
