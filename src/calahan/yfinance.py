"""A Python interface to the Yahoo! Finance API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final, Self

from ._yasync_client import YAsyncClient
from .yautocomplete import YAutocomplete
from .yquote import YQuote

if TYPE_CHECKING:
    from types import TracebackType

    import httpx

_QUOTE_API: Final[str] = "/v7/finance/quote"
_AUTOCOMPLETE_API: Final[str] = "/v6/finance/autocomplete"


class YFinance:
    """A Python interface to the Yahoo! Finance API."""

    def __init__(
        self,
        *,
        quote_api: str | None = None,
        autocomplete_api: str | None = None,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        """Initialize the Yahoo! Finance API interface.

        Args:
            quote_api (str | None): The endpoint for quote retrieval.
                Defaults to None, which uses the standard Yahoo! Finance quote API.
            autocomplete_api (str | None): The endpoint for autocomplete retrieval.
                Defaults to None, which uses the standard Yahoo! Finance autocomplete
                API.
            timeout (httpx.Timeout | None): The timeout configuration for HTTP requests.
                Defaults to None, which uses the default timeout settings.
        """

        self._yclient = YAsyncClient(timeout=timeout)
        self._quote_api: Final[str] = quote_api or _QUOTE_API
        self._autocomplete_api: Final[str] = autocomplete_api or _AUTOCOMPLETE_API

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

        Raises:
            ValueError: If no symbols are provided.
        """

        logger = logging.getLogger(__name__)
        if len(symbols) == 0:
            error_msg = "No symbols provided"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # call YClient.call with symbols stripped of whitespace
        json_data: dict[str, Any] = await self._yclient.call(
            self._quote_api, {"symbols": ",".join([s.strip() for s in symbols])}
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
            self._autocomplete_api, {"query": query}
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

    async def __aenter__(self) -> Self:
        await self.prime()
        return self

    async def __aexit__(
        self,
        exc_t: type[BaseException] | None,
        exc_v: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
