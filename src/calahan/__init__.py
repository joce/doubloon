"""Access real-time and historical financial market data from Yahoo Finance."""

import logging

from .enums import MarketState, OptionType, PriceAlertConfidence, QuoteType
from .exceptions import (
    CalahanError,
    MarketDataMalformedError,
    MarketDataRequestError,
    MarketDataUnavailableError,
)
from .types import ParamType
from .yfinance import YFinance
from .yquote import YQuote

# Add NullHandler to prevent errors if the application doesn't configure logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "CalahanError",
    "MarketDataMalformedError",
    "MarketDataRequestError",
    "MarketDataUnavailableError",
    "MarketState",
    "OptionType",
    "ParamType",
    "PriceAlertConfidence",
    "QuoteType",
    "YFinance",
    "YQuote",
]
__version__ = "0.1.1"
