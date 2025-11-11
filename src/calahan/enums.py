"""Provide enumerated types for financial data from Yahoo! Finance."""

from enum import Enum


class QuoteType(Enum):
    """Classification of financial instruments supported by Yahoo! Finance API.

    Attributes:
        EQUITY (str): Equity.
        INDEX (str): Index.
        OPTION (str): Option.
        CURRENCY (str): Currency.
        CRYPTOCURRENCY (str): Cryptocurrency.
        FUTURE (str): Future.
        ETF (str): ETF.
        MUTUALFUND (str): Mutual Fund.
    """

    EQUITY = "EQUITY"
    INDEX = "INDEX"
    OPTION = "OPTION"
    CURRENCY = "CURRENCY"
    CRYPTOCURRENCY = "CRYPTOCURRENCY"
    FUTURE = "FUTURE"
    ETF = "ETF"
    MUTUALFUND = "MUTUALFUND"
    PRIVATE_COMPANY = "PRIVATE_COMPANY"


class MarketState(Enum):
    """Trading session phases for financial markets in Yahoo! Finance.

    Attributes:
        PREPRE (str): Pre-pre market state.
        PRE (str): Pre market state;
            usually weekdays from 4:00am - 9:30am Eastern, excluding holidays.
        REGULAR (str): Regular market state;
            usually weekdays from 9:30am - 4:00pm Eastern, excluding holidays.
        POST (str): Post market state;
            usually weekdays from 4:00pm - 8:00pm Eastern, excluding holidays.
        POSTPOST (str): Post-post market.
        CLOSED (str): Closed market.
    """

    PREPRE = "PREPRE"
    PRE = "PRE"
    REGULAR = "REGULAR"
    POST = "POST"
    POSTPOST = "POSTPOST"
    CLOSED = "CLOSED"


class OptionType(Enum):
    """Classification of derivative contracts by right to buy/sell the underlying asset.

    Attributes:
        CALL (str): Call option.
        PUT (str): Put option.
    """

    CALL = "CALL"
    PUT = "PUT"


class PriceAlertConfidence(Enum):
    """Confidence level indicator for Yahoo! Finance price alerts with internal usage.

    Attributes:
        NONE (str): No confidence.
        LOW (str): Low confidence.
        HIGH (str): High confidence.
    """

    NONE = "NONE"
    LOW = "LOW"
    HIGH = "HIGH"
