"""Provide structured access to financial market quotes from Yahoo! Finance."""

from __future__ import annotations

import sys
from datetime import date, datetime
from functools import cached_property

from pydantic import BaseModel, Field, computed_field
from pydantic.alias_generators import to_camel

# These types are required in full for serialization purposes
from .enums import (  # noqa: TC001
    MarketState,
    OptionType,
    PriceAlertConfidence,
    QuoteType,
)

if sys.version_info >= (3, 11):
    from datetime import UTC as UTC_DT
    from zoneinfo import ZoneInfo

    UTC = UTC_DT
else:
    import pytz

    UTC = pytz.UTC


class YQuote(BaseModel):
    """Structured representation of financial market quote data from Yahoo! Finance."""

    model_config = {
        "frozen": True,  # Makes all fields read-only
        "str_strip_whitespace": True,  # Automatically strip whitespace from strings
        "alias_generator": to_camel,
    }

    ask: float | None = None
    """
    Lowest price a seller is willing to accept for the security.

    Applies to CURRENCY, EQUITY, ETF, FUTURE, INDEX and OPTION quotes.
    """

    ask_size: int | None = None
    """
    Number of units available at current ask price.

    Applies to CURRENCY, EQUITY, ETF and INDEX quotes.
    """

    average_analyst_rating: str | None = None
    """
    Consensus rating from financial analysts for the stock.

    Applies to EQUITY quotes.
    """

    average_daily_volume_10_day: int | None = None
    """
    Average number of shares traded each day over the last 10 days.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and MUTUALFUND
    quotes.
    """

    average_daily_volume_3_month: int | None = None
    """
    Average number of shares traded each day over the last 3 months.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and MUTUALFUND
    quotes.
    """

    bid: float | None = None
    """
    Highest price a buyer is willing to pay for the security.

    Applies to CURRENCY, EQUITY, ETF, FUTURE, INDEX and OPTION quotes.
    """

    bid_size: int | None = None
    """
    Total number of shares that buyers want to buy at the bid price.

    Applies to CURRENCY, EQUITY, ETF and INDEX quotes.
    """

    book_value: float | None = None
    """
    Net accounting value of a company's assets.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    circulating_supply: int | None = None
    """
    Number of cryptocurrency units currently in public circulation.

    Applies to CRYPTOCURRENCY quotes.
    """

    coin_image_url: str | None = None
    """
    URL of the image representing the cryptocurrency.

    Applies to CRYPTOCURRENCY quotes.
    """

    coin_market_cap_link: str | None = None
    """
    URL of the MarketCap site for the cryptocurrency.

    Applies to CRYPTOCURRENCY quotes.
    """

    contract_symbol: bool | None = None
    """
    Ticker symbol for a futures contract.

    Applies to FUTURE quotes.
    """

    crypto_tradeable: bool | None = None
    """
    Whether the cryptocurrency can be traded.

    Applies to CRYPTOCURRENCY quotes.
    """

    custom_price_alert_confidence: PriceAlertConfidence
    """
    Value whose meaning is not clear at the moment.

    Seen values have been NONE, LOW and HIGH.
    Applies to ALL quotes.
    """

    currency: str
    """
    Currency in which the security is traded.

    Applies to ALL quotes.
    """

    display_name: str | None = None
    """
    User-friendly name of the stock or security.

    Applies to EQUITY quotes.
    """

    dividend_date: date | None = None
    """
    Date when the company is expected to pay its next dividend.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    dividend_rate: float | None = None
    """
    Amount of dividends that a company is expected to pay over the next year.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    dividend_yield: float | None = None
    """
    Annual dividend as a percentage of the security's current price.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    earnings_timestamp: int | None = None
    """
    Raw timestamp value of the date and time of the company's earnings announcement.

    Applies to EQUITY quotes.
    """

    earnings_timestamp_end: int | None = None
    """
    Raw timestamp value of the date and time of the end of the company's earnings
    announcement.

    Applies to EQUITY quotes.
    """

    earnings_timestamp_start: int | None = None
    """
    Raw timestamp value of the date and time of the start of the company's earnings
    announcement.

    Applies to EQUITY quotes.
    """

    eps_current_year: float | None = None
    """
    Company's earnings per share (EPS) for the current year.

    Applies to EQUITY quotes.
    """

    eps_forward: float | None = None
    """
    Company's projected earnings per share (EPS) for the next fiscal year.

    Applies to EQUITY quotes.
    """

    eps_trailing_twelve_months: float | None = None
    """
    Company's earnings per share (EPS) for the past 12 months.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    esg_populated: bool
    """
    Availability status of ESG ratings data.

    Applies to ALL quotes.
    """
    exchange: str
    """
    Securities exchange on which the security is traded.

    Applies to ALL quotes.
    """

    exchange_data_delayed_by: int
    """
    Delay in data from the exchange, typically in minutes.

    Applies to ALL quotes.
    """

    exchange_timezone_name: str
    """
    Name of the timezone of the exchange.

    Applies to ALL quotes.
    """

    exchange_timezone_short_name: str
    """
    Short name of the timezone of the exchange.

    Applies to ALL quotes.
    """

    expire_date: date | None = None
    """
    Date on which the option contract expires.

    Applies to OPTION quotes.
    """

    expire_iso_date: str | None = None
    """
    Date on which the option contract expires, in ISO 8601 format.

    Applies to OPTION quotes.
    """

    fifty_day_average: float | None = None
    """
    Average closing price of the stock over the past 50 trading days.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and MUTUALFUND
    quotes.
    """

    fifty_day_average_change: float | None = None
    """
    Change in the 50-day average price from the previous trading day.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and MUTUALFUND
    quotes.
    """

    fifty_day_average_change_percent: float | None = None
    """
    Percent change in the 50-day average price from the previous trading day.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and MUTUALFUND
    quotes.
    """

    fifty_two_week_change_percent: float | None = None
    """
    Percentage change in price over the past 52 weeks.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and MUTUALFUND
    quotes.
    """

    fifty_two_week_high: float
    """
    Highest price the stock has traded at in the past 52 weeks.

    Applies to ALL quotes.
    """

    fifty_two_week_high_change: float
    """
    Change in the 52-week high price from the previous trading day.

    Applies to ALL quotes.
    """

    fifty_two_week_high_change_percent: float
    """
    Percent change in the 52-week high price from the previous trading day.

    Applies to ALL quotes.
    """

    fifty_two_week_low: float
    """
    Lowest price the stock has traded at in the past 52 weeks.

    Applies to ALL quotes.
    """

    fifty_two_week_low_change: float
    """
    Change in the 52-week low price from the previous trading day.

    Applies to ALL quotes.
    """

    fifty_two_week_low_change_percent: float
    """
    Percent change in the 52-week low price from the previous trading day.

    Applies to ALL quotes.
    """

    fifty_two_week_range: str
    """
    Trading price range over the past 52 weeks.

    Applies to ALL quotes.
    """

    financial_currency: str | None = None
    """
    Currency in which the company reports its financial results.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    first_trade_date_milliseconds: int
    """
    Raw value of the date and time of first trade of this security, in milliseconds.

    Applies to ALL quotes.
    """

    forward_pe: float | None = None
    """
    Projected price-to-earnings ratio for the next 12 months.

    Applies to EQUITY quotes.
    """

    from_currency: str | None = None
    """
    Base currency in exchange pair.

    Applies to CRYPTOCURRENCY quotes.
    """

    full_exchange_name: str
    """
    Full name of the securities exchange on which the security is traded.

    Applies to ALL quotes.
    """

    gmt_off_set_milliseconds: int
    """
    Offset from GMT of the exchange, in milliseconds.

    Applies to ALL quotes.
    """

    head_symbol_as_string: str | None = None
    """
    Symbol of the contract's underlying security.

    Applies to OPTION quotes.
    """

    ipo_expected_date: date | None = None
    """
    Expected date of the initial public offering (IPO).

    Applies to EQUITY quotes.
    """

    language: str
    """
    Language in which financial results are reported.

    Applies to ALL quotes.
    """

    last_market: str | None = None
    """
    Last market in which the security was traded.

    Applies to CRYPTOCURRENCY quotes.
    """

    logo_url: str | None = None
    """
    URL of the company's logo.

    Applies to CRYPTOCURRENCY quotes.
    """

    long_name: str | None = None
    """
    Official name of the company.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, INDEX and MUTUALFUND quotes.
    """

    market: str
    """
    Primary market for the security.

    Applies to ALL quotes.
    """

    market_cap: int | None = None
    """
    Total market value of the security in trading currency.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    market_state: MarketState
    """
    Current state of the market for a security.

    Applies to ALL quotes.
    """

    message_board_id: str | None = None
    """
    Identifier for the Yahoo! Finance message board for this security.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, INDEX and MUTUALFUND quotes.
    """

    name_change_date: date | None = None
    """
    Date on which the company last changed its name.

    Applies to EQUITY quotes.
    """

    net_assets: float | None = None
    """
    Total net assets of the company.

    Applies to ETF and MUTUALFUND quotes.
    """

    net_expense_ratio: float | None = None
    """
    Ratio of total expenses to total net assets.

    Applies to ETF and MUTUALFUND quotes.
    """

    open_interest: int | None = None
    """
    Total number of open contracts on a futures or options market.

    Applies to FUTURE and OPTION quotes.
    """

    option_type: OptionType | None = None
    """
    Type of option.

    Applies to OPTION quotes.
    """

    post_market_change: float | None = None
    """
    Change in the security's price in post-market trading.

    Applies to ALL quotes.
    """

    post_market_change_percent: float | None = None
    """
    Percent change in the security's price in post-market trading.

    Applies to ALL quotes.
    """

    post_market_price: float | None = None
    """
    Price of the security in post-market trading.

    Applies to ALL quotes.
    """

    post_market_time: int | None = None
    """
    Raw timestamp of the most recent post-market trade.

    Applies to ALL quotes.
    """

    pre_market_change: float | None = None
    """
    Change in the security's price in pre-market trading.

    Applies to ALL quotes.
    """

    pre_market_change_percent: float | None = None
    """
    Percent change in the security's price in pre-market trading.

    Applies to ALL quotes.
    """

    pre_market_price: float | None = None
    """
    Price of the security in pre-market trading.

    Applies to ALL quotes.
    """

    pre_market_time: int | None = None
    """
    Raw timestamp of the most recent pre-market trade.

    Applies to ALL quotes.
    """

    prev_name: str | None = None
    """
    Name of the company prior to its most recent name change.

    Applies to EQUITY quotes.
    """

    price_eps_current_year: float | None = None
    """
    Current-year price-to-earnings ratio.

    Applies to EQUITY quotes.
    """

    price_hint: int
    """
    Decimal precision indicator for price values.

    Applies to ALL quotes.
    """

    price_to_book: float | None = None
    """
    Market value relative to book value per share.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    quote_source_name: str | None = None
    """
    Name of the source providing the quote.

    Applies to ALL quotes.
    """

    quote_type: QuoteType
    """
    Type of quote.

    Applies to ALL quotes.
    """

    region: str
    """
    Region in which the company is located.

    Applies to ALL quotes.
    """

    regular_market_change: float
    """
    Change in the security's price in regular trading.

    Applies to ALL quotes.
    """

    regular_market_change_percent: float
    """
    Percent change in the security's price in regular trading.

    Applies to ALL quotes.
    """

    regular_market_day_high: float | None = None
    """
    Highest price during regular trading session.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and OPTION quotes.
    """

    regular_market_day_low: float | None = None
    """
    Lowest price during regular trading session.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and OPTION quotes.
    """

    regular_market_day_range: str | None = None
    """
    Price range during regular trading session.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and OPTION quotes.
    """

    regular_market_open: float | None = None
    """
    Opening price for regular trading session.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and OPTION quotes.
    """

    regular_market_previous_close: float
    """
    Closing price of the security in the previous regular trading session.

    Applies to ALL quotes.
    """

    regular_market_price: float
    """
    Latest price from regular trading session.

    Applies to ALL quotes.
    """

    regular_market_time: int
    """
    Raw timestamp of the most recent trade in the regular trading session.

    Applies to ALL quotes.
    """
    regular_market_volume: int | None = None
    """
    Number of units traded in regular session.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and OPTION quotes.
    """

    shares_outstanding: int | None = None
    """
    Number of shares currently held by all shareholders.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    short_name: str
    """
    Short, user-friendly name for the stock or security.

    Applies to ALL quotes.
    """

    source_interval: int
    """
    Interval at which the data source provides updates, in seconds.

    Applies to ALL quotes.
    """

    start_date: date | None = None
    """
    Date on which the coin started trading.

    Applies to CRYPTOCURRENCY quotes.
    """

    strike: float | None = None
    """
    Contractually specified price for options exercise.

    Applies to OPTION quotes.
    """

    symbol: str
    """
    Ticker symbol of the security.

    Applies to ALL quotes.
    """

    to_currency: str | None = None
    """
    Counter currency in exchange pair.

    Applies to CRYPTOCURRENCY quotes.
    """

    tradeable: bool
    """
    Whether the security is currently tradeable.

    Applies to ALL quotes.
    """

    trailing_annual_dividend_rate: float | None = None
    """
    Dividend payment per share over the past 12 months.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    trailing_annual_dividend_yield: float | None = None
    """
    Dividend yield over the past 12 months.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    trailing_pe: float | None = Field(None, alias="trailingPE")
    """
    Trailing price-to-earnings ratio based on past twelve-month results.

    Applies to EQUITY, ETF and MUTUALFUND quotes.
    """

    trailing_three_month_nav_returns: float | None = None
    """
    Trailing 3-month net asset value (NAV) returns.

    Applies to ETF quotes.
    """

    trailing_three_month_returns: float | None = None
    """
    Trailing 3-month returns.

    Applies to ETF and MUTUALFUND quotes.
    """

    triggerable: bool
    """
    Internal Yahoo! Finance flag with undocumented and unknown purpose.

    Applies to ALL quotes.
    """

    two_hundred_day_average: float | None = None
    """
    Average closing price of the stock over the past 200 trading days.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and MUTUALFUND
    quotes.
    """

    two_hundred_day_average_change: float | None = None
    """
    Change in the 200-day average price from the previous trading day.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and MUTUALFUND
    quotes.
    """

    two_hundred_day_average_change_percent: float | None = None
    """
    Percent change in the 200-day average price from the previous trading day.

    Applies to CRYPTOCURRENCY, CURRENCY, EQUITY, ETF, FUTURE, INDEX and MUTUALFUND
    quotes.
    """

    type_disp: str
    """
    User-friendly representation of the QuoteType.

    Applies to ALL quotes.
    """

    underlying_exchange_symbol: str | None = None
    """
    Exchange symbol for the underlying asset's trading venue.

    Applies to FUTURE quotes.
    """

    underlying_short_name: str | None = None
    """
    Short name of the underlying security of a derivative.

    Applies to OPTION quotes.
    """

    underlying_symbol: str | None = None
    """
    Ticker symbol of the underlying security of a derivative.

    Applies to FUTURE and OPTION quotes.
    """

    volume_24_hr: int | None = None
    """
    Total trading volume of a cryptocurrency in the past 24 hours.

    Applies to CRYPTOCURRENCY quotes.
    """

    volume_all_currencies: int | None = None
    """
    Aggregate 24-hour volume across all currency pairs.

    Applies to CRYPTOCURRENCY quotes.
    """

    ytd_return: float | None = None
    """
    Year-to-date return on the security.

    Applies to ETF and MUTUALFUND quotes.
    """

    ###
    # Computed fields for datetime conversions
    ###

    @computed_field
    @cached_property
    def earnings_datetime(self) -> datetime | None:
        """Date and time of the company's earnings announcement.

        Applies to EQUITY quotes.
        """
        return self._get_datetime(self.earnings_timestamp)

    @computed_field
    @cached_property
    def earnings_datetime_end(self) -> datetime | None:
        """Date and time of the end of the company's earnings announcement.

        Applies to EQUITY quotes.
        """
        return self._get_datetime(self.earnings_timestamp_end)

    @computed_field
    @cached_property
    def earnings_datetime_start(self) -> datetime | None:
        """Date and time of the start of the company's earnings announcement.

        Applies to EQUITY quotes.
        """
        return self._get_datetime(self.earnings_timestamp_start)

    @computed_field
    @cached_property
    def first_trade_datetime(self) -> datetime:
        """Date and time of the first trade of this security.

        Applies to ALL quotes.
        """
        timestamp_seconds: int = self.first_trade_date_milliseconds // 1000
        microseconds: int = (self.first_trade_date_milliseconds % 1000) * 1000
        if sys.version_info >= (3, 11):
            tz_info: ZoneInfo = ZoneInfo(self.exchange_timezone_name)
            return datetime.fromtimestamp(timestamp_seconds, tz_info).replace(
                microsecond=microseconds
            )

        tz_info = pytz.timezone(self.exchange_timezone_name)
        return datetime.fromtimestamp(timestamp_seconds, tz_info).replace(
            microsecond=microseconds
        )

    @computed_field
    @cached_property
    def post_market_datetime(self) -> datetime | None:
        """Date and time of the most recent post-market trade.

        Applies to ALL quotes.
        """
        return self._get_datetime(self.post_market_time)

    @computed_field
    @cached_property
    def pre_market_datetime(self) -> datetime | None:
        """Date and time of the most recent pre-market trade.

        Applies to ALL quotes.
        """
        return self._get_datetime(self.pre_market_time)

    @computed_field
    @cached_property
    def regular_market_datetime(self) -> datetime | None:
        """Date and time of the most recent trade in the regular trading session.

        Applies to ALL quotes.
        """
        return self._get_datetime(self.regular_market_time)

    def _get_datetime(self, timestamp: int | None) -> datetime | None:
        """Convert a timestamp in seconds to a timezone-aware datetime object.

        Args:
            timestamp (int | None): Timestamp in UTC or None

        Returns:
            datetime | None: Timezone-aware datetime object, or None if input is None
        """

        if timestamp is None:
            return None

        if sys.version_info >= (3, 11):
            tz_info: ZoneInfo = ZoneInfo(self.exchange_timezone_name)

            return datetime.fromtimestamp(timestamp, tz_info)

        tz_info = pytz.timezone(self.exchange_timezone_name)

        return datetime.fromtimestamp(timestamp).astimezone(tz_info)

    def __str__(self) -> str:
        """Return string representation of the financial quote.

        Returns:
            str: Formatted as 'symbol: price (percent%) -- datetime'.
        """

        return (
            f"YQuote({self.symbol}: {self.regular_market_price} "
            f"({self.regular_market_change_percent:.2f}%) "
            f"-- {self.regular_market_datetime:%Y-%m-%d %H:%M})"
        )
