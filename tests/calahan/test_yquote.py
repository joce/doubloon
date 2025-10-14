"""Validate The behavior of the `YQuote` class."""

from typing import TYPE_CHECKING

from calahan.enums import MarketState, QuoteType
from tests.fake_yfinance import FakeYFinance

if TYPE_CHECKING:
    from calahan import YQuote


async def test_yquote_values() -> None:
    """Ensure the values are read properly for all versions of Python."""

    aapl_quote: YQuote
    gold_fut: YQuote
    aapl_quote, gold_fut, btc_usd = await FakeYFinance().retrieve_quotes(
        ["AAPL", "GC=F", "BTC-USD"]
    )
    assert gold_fut.expire_date is not None
    assert gold_fut.expire_date.strftime("%Y-%m-%d %H:%M:%S") == "2023-12-27 00:00:00"
    assert gold_fut.quote_type == QuoteType.FUTURE
    assert gold_fut.market_state == MarketState.REGULAR

    assert btc_usd.volume_24_hr == 16038881280  # noqa: PLR2004

    assert aapl_quote.earnings_datetime is not None
    assert aapl_quote.quote_type == QuoteType.EQUITY
    assert aapl_quote.trailing_pe == 29.757748  # noqa: PLR2004
    assert aapl_quote.market_state == MarketState.REGULAR

    assert (
        aapl_quote.earnings_datetime.strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-02 17:00:00"
    )
