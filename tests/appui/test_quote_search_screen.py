"""Tests for quote search helpers."""

from __future__ import annotations

from appui.quote_search_screen import QuoteSearchScreen
from calahan import QuoteType, YSearchQuote

# pyright: reportPrivateUsage=none


def _quote_factory(**overrides: object) -> YSearchQuote:
    base: dict[str, object] = {
        "exchange": "NMS",
        "exchDisp": "NasdaqGS",
        "index": "quotes",
        "isYahooFinance": True,
        "quoteType": QuoteType.EQUITY,
        "score": 1.0,
        "shortname": "Example",
        "symbol": "EXAMPLE",
        "typeDisp": "Equity",
        "longname": "Example Corp",
    }
    base.update(overrides)
    return YSearchQuote.model_validate(base)


def test_format_quote_option_prefers_long_name() -> None:
    quote = _quote_factory(symbol="AAPL", longname="Apple Inc.", shortname="Apple")

    assert (
        QuoteSearchScreen._format_quote_option(quote) == "AAPL — Apple Inc. (NasdaqGS)"
    )
