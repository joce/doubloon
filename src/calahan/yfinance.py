"""A Python interface to the Yahoo! Finance API."""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import TYPE_CHECKING, Any, Final

from ._yasync_client import YAsyncClient
from .yquote import YQuote
from .ysearch_result import YSearchResult

if TYPE_CHECKING:
    from types import TracebackType

    import httpx

    from .types import ParamType

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


_LOGGER = logging.getLogger(__name__)


class YFinance:
    """A Python interface to the Yahoo! Finance API."""

    _QUOTE_API: Final[str] = "/v7/finance/quote"
    _SEARCH_API: Final[str] = "/v1/finance/search"

    _MAX_SYMBOLS_PER_REQUEST: Final[int] = 10

    def __init__(
        self,
        *,
        quote_api: str | None = None,
        search_api: str | None = None,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        """Initialize the Yahoo! Finance API interface.

        Args:
            quote_api (str | None): The endpoint for quote retrieval.
                Defaults to None, which uses the standard Yahoo! Finance quote API.
            search_api (str | None): The endpoint for search query.
                Defaults to None, which uses the standard Yahoo! Finance search
                API.
            timeout (httpx.Timeout | None): The timeout configuration for HTTP requests.
                Defaults to None, which uses the default timeout settings.
        """

        self._yclient = YAsyncClient(timeout=timeout)
        self._quote_api: Final[str] = quote_api or YFinance._QUOTE_API
        self._search_api: Final[str] = search_api or YFinance._SEARCH_API

    async def prime(self) -> None:
        """Prime the YFinance client."""

        await self._yclient.prime()

    async def aclose(self) -> None:
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

        async def _retrieve_quote_batch(batch: list[str]) -> list[YQuote]:
            params: dict[str, ParamType] = {"symbols": ",".join(batch)}
            payload: dict[str, Any] = await self._yclient.call(self._quote_api, params)

            if "quoteResponse" not in payload:
                _LOGGER.error("No quote response from Yahoo!")
                return []

            quote_response = payload["quoteResponse"]

            if "error" in quote_response and quote_response["error"] is not None:
                _LOGGER.error(
                    "Error getting response data from Yahoo!: %s",
                    quote_response["error"]["description"],
                )
                return []

            return [
                YQuote.model_validate(q)
                for q in quote_response.get("result", [])
                if q is not None
            ]

        normalized_symbols = [s.strip().upper() for s in symbols if s.strip()]

        if len(normalized_symbols) == 0:
            error_msg = "No symbols provided"
            _LOGGER.error(error_msg)
            raise ValueError(error_msg)

        batches = [
            normalized_symbols[i : i + YFinance._MAX_SYMBOLS_PER_REQUEST]
            for i in range(
                0, len(normalized_symbols), YFinance._MAX_SYMBOLS_PER_REQUEST
            )
        ]

        tasks = [_retrieve_quote_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        quote_map: dict[str, YQuote] = {}
        for batch, result in zip(batches, batch_results, strict=True):
            if isinstance(result, Exception):
                _LOGGER.error(
                    "Quote batch failed for symbols %s: %s",
                    batch,
                    result,
                )
                continue
            if isinstance(result, list):
                for quote in result:
                    quote_map.setdefault(quote.symbol, quote)

        return [
            quote_map[symbol] for symbol in normalized_symbols if symbol in quote_map
        ]

    async def search(  # noqa: PLR0913
        self,
        search_term: str,
        *,
        lang: str = "en-US",
        region: str = "US",
        recommend_count: int = 6,
        quotes_count: int = 7,
        enable_news: bool = False,
        news_count: int = 3,
        news_query_id: str = "news_cie_vespa",
        enable_lists: bool = False,
        lists_count: int = 2,
        enable_nav_links: bool = False,
        enable_research_reports: bool = False,
        enable_cultural_assets: bool = False,
        enable_private_company: bool = True,
        enable_logo_url: bool = False,
        enable_fuzzy_query: bool = False,
        enable_enhanced_trivial_query: bool | None = None,
        enable_ccc_boost: bool = True,
        quotes_query_id: str = "tss_match_phrase_query",
        multi_quote_query_id: str = "multi_quote_single_token_query",
        enable_cb: bool = False,
    ) -> YSearchResult:
        """Search for the given search term.

        Args:
            search_term (str): The term to search for.
            lang (str): Language for the search results. Defaults to 'en-US'.
            region (str): Region for the search results. Defaults to 'US'.
            recommend_count (int): Number of recommendations to return. Defaults to 6.
            quotes_count (int): Number of quote results to return. Defaults to 7.
            enable_news (bool): Whether to enable news results. Defaults to False.
            news_query_id (str): Query ID for news. Defaults to 'news_cie_vespa'. Not
                recommended to change unless necessary.
            news_count (int): Number of news articles to return. Defaults to 3.
            enable_lists (bool): Whether to enable lists. Defaults to False.
            lists_count (int): Number of lists to return. Defaults to 2.
            enable_nav_links (bool): Whether to enable navigation links. Defaults to
                False.
            enable_research_reports (bool): Whether to enable research reports. Defaults
                to False.
            enable_cultural_assets (bool): Whether to enable cultural assets. Defaults
                to False.
            enable_private_company (bool): Whether to include private companies.
                Defaults to True.
            enable_logo_url (bool): Whether to include logo URLs in the results.
                Defaults to False.
            enable_fuzzy_query (bool): Whether to enable fuzzy query matching. Defaults
            enable_enhanced_trivial_query (bool | None): Whether to enable enhanced
                trivial query matching. Defaults to None, which enables it only for
                search terms if they are less than 3 characters.
            enable_ccc_boost (bool): Whether to enable CCC boost (??). Defaults to True.
                Not recommended to change unless necessary.
            quotes_query_id (str): Query ID for quotes. Defaults to
                'tss_match_phrase_query'. Not recommended to change unless necessary.
            multi_quote_query_id (str): Query ID for multi-quote searches. Defaults to
                'multi_quote_single_token_query'. Not recommended to change unless
                necessary.
            enable_cb (bool): Whether to enable content block (??) results. Defaults to
                False.

        Returns:
            YSearchResult: The search results for the given search term.

        Raises:
            ValueError: If no search term is provided.
        """

        search_term = search_term.strip()
        if not search_term:
            error_msg = "No symbols provided"
            _LOGGER.error(error_msg)
            raise ValueError(error_msg)

        trivial_search_threshold = 3
        json_data: dict[str, Any] = await self._yclient.call(
            self._search_api,
            {
                "q": search_term,
                "lang": lang,
                "region": region,
                "enableFuzzyQuery": enable_fuzzy_query,
                "enableEnhancedTrivialQuery": (
                    enable_enhanced_trivial_query
                    or len(search_term) < trivial_search_threshold
                ),
                "recommendCount": recommend_count,
                "quotesCount": quotes_count,
                "quotesQueryId": quotes_query_id,
                "multiQuoteQueryId": multi_quote_query_id,
                "enableCb": enable_cb,
                "enableNews": enable_news,
                "newsCount": news_count,
                "newsQueryId": news_query_id,
                "enableLists": enable_lists,
                "listsCount": lists_count,
                "enableNavLinks": enable_nav_links,
                "enableResearchReports": enable_research_reports,
                "enableCulturalAssets": enable_cultural_assets,
                "enablePrivateCompany": enable_private_company,
                "enableCccBoost": enable_ccc_boost,
                "enableLogoUrl": enable_logo_url,
            },
            use_crumb=False,
        )

        return YSearchResult.model_validate(json_data)

    async def __aenter__(self) -> Self:
        await self.prime()
        return self

    async def __aexit__(
        self,
        exc_t: type[BaseException] | None,
        exc_v: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()
