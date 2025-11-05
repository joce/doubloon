"""Fake YFinance client that pulls data from a test data file."""

from __future__ import annotations

import json
from typing import Any

from anyio import Path

from calahan import YFinance, YQuote, YSearchResult


class FakeYFinance(YFinance):
    """Fake YFinance client that pulls data from a test data file."""

    # pylint: disable=super-init-not-called
    def __init__(self) -> None:
        """Initialize the fake YFinance client."""

        self._quotes: list[YQuote] = []
        self._search_results: YSearchResult | None = None

    @staticmethod
    async def _load_test_data(filename: str) -> Any:  # noqa: ANN401
        """Load test data from the given file."""

        current_path = await Path(__file__).resolve()
        test_data_file = current_path.parent / filename
        json_text = await test_data_file.read_text(encoding="utf-8")
        return json.loads(json_text)

    async def retrieve_quotes(self, symbols: list[str]) -> list[YQuote]:
        """Retrieve quotes for the given symbols.

        In this implementation, the quotes are pulled from the test data file.

        Args:
            symbols (list[str]): The symbols to get quotes for.

        Returns:
            list[YQuote]: The quotes for the given symbols.
        """

        if not self._quotes:
            json_data = await self._load_test_data("test_yquote.json")
            self._quotes = [
                YQuote.model_validate(q)
                for q in json_data["quoteResponse"]["result"]
                if q is not None
            ]
        # return the quotes where the symbol is in the list of symbols
        return [q for q in self._quotes if q.symbol in symbols]

    async def search(self, search_term: str) -> YSearchResult:
        """Search for the given search term.

        In this implementation, the search results are pulled from the test data file.

        Args:
            search_term (str): The term to search for.

        Returns:
            YSearchResult: The search results for the given search term.
        """

        assert search_term.strip() == "BTC"  # only support "BTC" for tests

        if not self._search_results:

            # Get the directory of the path of this file.
            json_data = await self._load_test_data("test_ysearch_btc.json")
            self._search_results = YSearchResult.model_validate(json_data)

        return self._search_results
