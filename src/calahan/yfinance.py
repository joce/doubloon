"""A Python interface to the Yahoo! Finance API."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any, Final

from ._yasync_client import YAsyncClient
from .yquote import YQuote
from .ysearch_result import YSearchResult

if TYPE_CHECKING:
    from types import TracebackType

    import httpx

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

_QUOTE_API: Final[str] = "/v7/finance/quote"
_SEARCH_API: Final[str] = "/v1/finance/search"

_LOGGER = logging.getLogger(__name__)


class YFinance:
    """A Python interface to the Yahoo! Finance API."""

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
        self._quote_api: Final[str] = quote_api or _QUOTE_API
        self._search_api: Final[str] = search_api or _SEARCH_API

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

        if len(symbols) == 0:
            error_msg = "No symbols provided"
            _LOGGER.error(error_msg)
            raise ValueError(error_msg)

        # call YClient.call with symbols stripped of whitespace
        json_data: dict[str, Any] = await self._yclient.call(
            self._quote_api, {"symbols": ",".join([s.strip() for s in symbols])}
        )

        if "quoteResponse" not in json_data:
            _LOGGER.error("No quote response from Yahoo!")
            return []

        if (
            "error" in json_data["quoteResponse"]
            and json_data["quoteResponse"]["error"] is not None
        ):
            _LOGGER.error(
                "Error getting response data from Yahoo!: %s",
                json_data["quoteResponse"]["error"]["description"],
            )
            return []

        return [
            YQuote.model_validate(q)
            for q in json_data["quoteResponse"]["result"]
            if q is not None
        ]

    async def search(  # noqa: PLR0913
        self,
        search_term: str,
        *,
        lang: str = "en-US",
        region: str = "US",
        enable_fuzzy_query: bool = False,
        enable_enhanced_trivial_query: bool | None = None,
        recommend_count: int = 6,
        quotes_count: int = 7,
        quotes_query_id: str = "tss_match_phrase_query",
        multi_quote_query_id: str = "multi_quote_single_token_query",
        enable_cb: bool = False,
        enable_news: bool = False,
        news_count: int = 3,
        news_query_id: str = "news_cie_vespa",
        enable_lists: bool = False,
        lists_count: int = 2,
        enable_nav_links: bool = False,
        enable_research_reports: bool = False,
        enable_cultural_assets: bool = False,
        enable_private_company: bool = True,
        enable_ccc_boost: bool = True,
        enable_logo_url: bool = False,
    ) -> YSearchResult:
        """Search for the given search term.

        Args:
            search_term (str): The term to search for.
            lang (str): Language for the search results. Defaults to 'en-US'.
            region (str): Region for the search results. Defaults to 'US'.
            enable_fuzzy_query (bool): Whether to enable fuzzy query matching. Defaults
            enable_enhanced_trivial_query (bool | None): Whether to enable enhanced
                trivial query matching. Defaults to None, which enables it only for
                search terms if they are less than 3 characters.
            recommend_count (int): Number of recommendations to return. Defaults to 6.
            quotes_count (int): Number of quote results to return. Defaults to 7.
            quotes_query_id (str): Query ID for quotes. Defaults to
                'tss_match_phrase_query'. Not recommended to change unless necessary.
            multi_quote_query_id (str): Query ID for multi-quote searches. Defaults to
                'multi_quote_single_token_query'. Not recommended to change unless
                necessary.
            enable_cb (bool): Whether to enable content block (??) results. Defaults to
                False.
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
            enable_ccc_boost (bool): Whether to enable CCC boost. Defaults to True. Not
                recommended to change unless necessary.
            enable_logo_url (bool): Whether to include logo URLs in the results.
                Defaults to False.

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
        json_data: dict[str, Any] = await self._yclient.call(
            self._search_api,
            {
                "q": search_term,
                "lang": lang,
                "region": region,
                "enableFuzzyQuery": enable_fuzzy_query,
                "enableEnhancedTrivialQuery": (
                    enable_enhanced_trivial_query or len(search_term) < 3
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

        if "quotes" not in json_data:
            _LOGGER.error("No quote response from Yahoo!")
            return YSearchResult(count=0, quotes=[])

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
