"""A Python interface to the Yahoo! Finance API."""

from __future__ import annotations

import logging
from typing import Any, Final

from ._yasync_client import YAsyncClient
from .yautocomplete import YAutocomplete
from .yquote import YQuote


class YFinance:
    """A Python interface to the Yahoo! Finance API."""

    _QUOTE_API: Final[str] = "/v7/finance/quote"
    _AUTOCOMPLETE_API: Final[str] = "/v6/finance/autocomplete"

    def __init__(self) -> None:
        """Initialize the Yahoo! Finance API interface."""

        self._yclient = YAsyncClient()

    async def prime(self) -> None:
        """Prime the YFinance client."""

        await self._yclient.prime()

    async def close(self) -> None:
        """Close the YFinance client."""
        await self._yclient.aclose()

    async def retrieve_quotes(self, symbols: list[str]) -> list[YQuote]:
        """Retrieve quotes for the given symbols.

        Args:
            symbols (list[str]): The symbols to get quotes for.

        Returns:
            list[YQuote]: The quotes for the given symbols.
        """

        logger = logging.getLogger(__name__)
        if len(symbols) == 0:
            logger.error("No symbols provided")
            return []

        # call YClient.call with symbols stripped of whitespace
        json_data: dict[str, Any] = await self._yclient.call(
            self._QUOTE_API, {"symbols": ",".join([s.strip() for s in symbols])}
        )

        if "quoteResponse" not in json_data:
            logger.error("No quote response from Yahoo!")
            return []

        if (
            "error" in json_data["quoteResponse"]
            and json_data["quoteResponse"]["error"] is not None
        ):
            logger.error(
                "Error getting response data from Yahoo!: %s",
                json_data["quoteResponse"]["error"]["description"],
            )
            return []

        return [
            YQuote.model_validate(q)
            for q in json_data["quoteResponse"]["result"]
            if q is not None
        ]

    async def retrieve_autocompletes(
        self, query: str
    ) -> tuple[str, list[YAutocomplete]]:
        """Retrieve autocomplete entries for the given query.

        Args:
            query (str): The query to get autocomplete entries for.

        Returns:
            list[YAutocomplete]: The autocomplete entries for the given query.
        """

        logger = logging.getLogger(__name__)

        json_data: dict[str, Any] = await self._yclient.call(
            self._AUTOCOMPLETE_API, {"query": query}
        )

        if "ResultSet" not in json_data:
            logger.error("No autocomplete response from Yahoo!")
            return (query, [])

        return (
            query,
            [
                YAutocomplete(q)
                for q in json_data["ResultSet"]["Result"]
                if q is not None
            ],
        )
