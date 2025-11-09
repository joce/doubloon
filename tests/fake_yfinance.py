"""Fake YFinance client that pulls data from a test data file."""

# pylint: disable=missing-param-doc
# pylint: disable=missing-return-doc
# pylint: disable=arguments-differ

from __future__ import annotations

import json
import sys
from typing import Any

from anyio import Path

from calahan import YFinance, YQuote, YSearchResult

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


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

    @override
    async def retrieve_quotes(self, symbols: list[str]) -> list[YQuote]:
        """Retrieve prerecorded quotes for selected symbols.

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

    async def search(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        search_term: str,
    ) -> YSearchResult:
        """Return prerecorded search results for a given term.

        This helper intentionally accepts fewer parameters than ``YFinance.search``
        because it only exists to serve deterministic fixtures in tests.
        """

        assert (
            search_term.strip().lower()
            == "mortgage"  # only support "mortgage" for tests
        )

        if not self._search_results:
            json_data = await self._load_test_data("test_ysearch.json")
            self._search_results = YSearchResult.model_validate(json_data)

        return self._search_results
