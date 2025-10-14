"""Provide structured access to autocomplete from Yahoo! Finance."""

from __future__ import annotations

from typing import Any

from .enums import QuoteType


class YAutocomplete:
    """Provide structured access to autocomplete from Yahoo! Finance."""

    @property
    def exchange(self) -> str:
        """Get the exchange code."""

        return self._exchange

    @property
    def exchange_display(self) -> str:
        """Get the exchange display name."""

        return self._exchange_display

    @property
    def name(self) -> str:
        """Get the name of the financial instrument."""

        return self._name

    @property
    def symbol(self) -> str:
        """Get the symbol of the financial instrument."""

        return self._symbol

    @property
    def type(self) -> QuoteType:
        """Get the type of the financial instrument."""

        return self._type

    @property
    def type_display(self) -> str:
        """Get the type display name of the financial instrument."""

        return self._type_display

    def __init__(self, input_data: dict[str, Any]) -> None:
        """Create an autocomplete entry from Yahoo! Finance API response data.

        Args:
            input_data (dict[str, any]): the JSON data returned by the Yahoo! Finance
            API.
        """

        self._exchange: str = input_data.get("exch", "")
        self._exchange_display: str = input_data.get("exchDisp", "")
        self._name: str = input_data.get("name", "")
        self._symbol: str = input_data.get("symbol", "")
        self._type: QuoteType = YAutocomplete._to_quote_type(input_data.get("type", ""))
        self._type_display: str = input_data.get("typeDisp", "")

    @classmethod
    def _to_quote_type(cls, type_str: str) -> QuoteType:
        """Convert the type string from Yahoo! Finance to a QuoteType enum value.

        Args:
            type_str (str): The type string from Yahoo! Finance.

        Returns:
            QuoteType: The corresponding QuoteType enum value.
        """

        # Types for Option, Currency, Cryptocurrency, Future, and ETF are not
        # currently mapped.
        mapping: dict[str, QuoteType] = {
            "S": QuoteType.EQUITY,
            "I": QuoteType.INDEX,
            "M": QuoteType.MUTUALFUND,
        }
        return mapping.get(type_str.upper(), QuoteType.EQUITY)
