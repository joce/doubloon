"""Fake YFinance client that pulls data from a test data file."""

from __future__ import annotations

import json

from anyio import Path

from calahan import YFinance, YQuote


class FakeYFinance(YFinance):
    """Fake YFinance client that pulls data from a test data file."""

    # pylint: disable=super-init-not-called
    def __init__(self) -> None:
        """Initialize the fake YFinance client."""

        self._quotes: list[YQuote] = []

    async def retrieve_quotes(self, symbols: list[str]) -> list[YQuote]:
        """Retrieve quotes for the given symbols.

        In this implementation, the quotes are pulled from the test data file.

        Args:
            symbols (list[str]): The symbols to get quotes for.

        Returns:
            list[YQuote]: The quotes for the given symbols.
        """

        if not self._quotes:
            # Get the directory of the path of this file.
            current_path = await Path(__file__).resolve()
            test_data_file = current_path.parent / "test_yquote.json"
            json_text = await test_data_file.read_text(encoding="utf-8")
            json_data = json.loads(json_text)
            self._quotes = [
                YQuote.model_validate(q)
                for q in json_data["quoteResponse"]["result"]
                if q is not None
            ]
        # return the quotes where the symbol is in the list of symbols
        return [q for q in self._quotes if q.symbol in symbols]
