"""Validate The behavior of the `YQuote` class."""

import zoneinfo
from datetime import datetime
from typing import TYPE_CHECKING

from calahan.enums import MarketState, QuoteType
from tests.fake_yfinance import FakeYFinance

if TYPE_CHECKING:
    from calahan import YQuote

# Values from the fake response for AAPL
_TRAILING_PE_VALUE_FROM_FAKE = 29.757748
_VOLUME_24_HR_VALUE_FROM_FAKE = 16038881280


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

    assert btc_usd.volume_24_hr == _VOLUME_24_HR_VALUE_FROM_FAKE

    assert aapl_quote.earnings_datetime is not None
    assert aapl_quote.quote_type == QuoteType.EQUITY
    assert aapl_quote.trailing_pe == _TRAILING_PE_VALUE_FROM_FAKE
    assert aapl_quote.market_state == MarketState.REGULAR

    tzinfo = zoneinfo.ZoneInfo("America/New_York")

    assert aapl_quote.earnings_datetime_start == datetime(
        2024, 1, 31, 5, 59, tzinfo=tzinfo
    )
    assert aapl_quote.earnings_datetime_end == datetime(2024, 2, 5, 7, 0, tzinfo=tzinfo)
    assert aapl_quote.first_trade_datetime == datetime(
        1980, 12, 12, 9, 30, tzinfo=tzinfo
    )
    assert aapl_quote.regular_market_datetime == datetime(
        2023, 11, 7, 14, 35, 45, tzinfo=tzinfo
    )
    assert aapl_quote.pre_market_datetime is None
    assert aapl_quote.post_market_datetime is None
    assert (
        aapl_quote.earnings_datetime.strftime("%Y-%m-%d %H:%M:%S")
        == "2023-11-02 17:00:00"
    )


async def test_yquote_str_repr() -> None:
    """Ensure the string and repr representations are correct."""

    (aapl_quote,) = await FakeYFinance().retrieve_quotes(["AAPL"])

    aapl_str = str(aapl_quote)
    assert aapl_str == "YQuote(AAPL: 182.415 (1.78%) -- 2023-11-07 14:35)"

    aapl_str = f"{aapl_quote!r}"
    assert aapl_str == "YQuote: AAPL"
