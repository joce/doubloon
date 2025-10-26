"""Validate the behavior of the `YFinance` class."""

# pyright: reportPrivateUsage=none
# pyright: reportUnknownVariableType=none

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from calahan import YFinance, YQuote


@dataclass
class _StubYAsyncClient:
    """Test double that mimics the YAsyncClient interface used by YFinance."""

    responses: list[Any] = field(default_factory=list)
    calls: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    prime_called: bool = False
    close_called: bool = False

    def queue_response(self, response: Any) -> None:  # noqa: ANN401
        """Queue a response that `call` will return."""

        self.responses.append(response)

    async def call(self, path: str, params: dict[str, str]) -> Any:  # noqa: ANN401
        """Return the next queued response and record invocation details."""

        self.calls.append((path, params))
        return self.responses.pop(0)

    async def prime(self) -> None:
        """Record that priming was requested."""

        self.prime_called = True

    async def aclose(self) -> None:
        """Record that closing was requested."""

        self.close_called = True


def _sample_quote_payload() -> dict[str, Any]:
    """Load a representative quote payload from test data."""

    test_data_path = Path(__file__).resolve().parents[1] / "test_data.json"
    data = test_data_path.read_text(encoding="utf-8")
    quotes = json.loads(data)["quoteResponse"]["result"]
    return next(q for q in quotes if q and q.get("symbol") == "AAPL")


@pytest.fixture
def yfinance_with_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[YFinance, _StubYAsyncClient]:
    """Provide a YFinance instance whose client is replaced with a stub."""

    yf = YFinance()
    stub = _StubYAsyncClient()
    monkeypatch.setattr(yf, "_yclient", stub, raising=False)
    return yf, stub


##########################
#  retrieve_quotes tests
##########################


@pytest.mark.asyncio
async def test_retrieve_quotes_requires_symbols(
    yfinance_with_stub: tuple[YFinance, _StubYAsyncClient],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """retrieve_quotes should raise and log when no symbols are supplied."""

    yf, _ = yfinance_with_stub

    with (
        caplog.at_level(logging.ERROR),
        pytest.raises(ValueError, match="No symbols provided"),
    ):
        await yf.retrieve_quotes([])
    assert "No symbols provided" in caplog.text


@pytest.mark.asyncio
async def test_retrieve_quotes_missing_quote_response(
    yfinance_with_stub: tuple[YFinance, _StubYAsyncClient],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Return an empty list and log when quoteResponse payload is absent."""

    yf, stub = yfinance_with_stub
    stub.queue_response({})

    with caplog.at_level(logging.ERROR):
        quotes = await yf.retrieve_quotes([" AAPL "])

    assert quotes == []
    assert stub.calls == [("/v7/finance/quote", {"symbols": "AAPL"})]
    assert "No quote response from Yahoo!" in caplog.text


@pytest.mark.asyncio
async def test_retrieve_quotes_error_block(
    yfinance_with_stub: tuple[YFinance, _StubYAsyncClient],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Return an empty list when the response reports an error."""

    yf, stub = yfinance_with_stub
    stub.queue_response(
        {
            "quoteResponse": {
                "error": {"description": "bad symbols"},
                "result": [],
            },
        }
    )

    with caplog.at_level(logging.ERROR):
        result = await yf.retrieve_quotes(["BAD"])

    assert result == []
    assert "bad symbols" in caplog.text


@pytest.mark.asyncio
async def test_retrieve_quotes_success_filters_none(
    yfinance_with_stub: tuple[YFinance, _StubYAsyncClient],
) -> None:
    """Valid responses yield YQuote objects and ignore null entries."""

    yf, stub = yfinance_with_stub
    payload = _sample_quote_payload()
    stub.queue_response(
        {
            "quoteResponse": {
                "error": None,
                "result": [payload, None],
            },
        }
    )

    quotes = await yf.retrieve_quotes(["AAPL", " "])

    assert len(quotes) == 1
    assert quotes[0].symbol == "AAPL"
    assert stub.calls == [("/v7/finance/quote", {"symbols": "AAPL,"})]


##############################
#  lifecycle helpers
##############################


@pytest.mark.asyncio
async def test_prime_and_close_delegate_to_client(
    yfinance_with_stub: tuple[YFinance, _StubYAsyncClient],
) -> None:
    """Prime and close should directly delegate to the underlying client."""

    yf, stub = yfinance_with_stub

    await yf.prime()
    await yf.close()

    assert stub.prime_called
    assert stub.close_called


@pytest.mark.asyncio
async def test_context_manager_primes_and_closes(
    yfinance_with_stub: tuple[YFinance, _StubYAsyncClient],
) -> None:
    """The async context manager primes on entry and closes on exit."""

    yf, stub = yfinance_with_stub

    async with yf as ctx:
        assert ctx is yf
        assert stub.prime_called

    assert stub.close_called


##########################
#  integration test
##########################


@pytest.mark.integration
async def test_yfinance_connects() -> None:
    """Test that the `YFinance` class connects to the Yahoo! Finance API."""

    try:
        yf = YFinance()
        await yf.prime()
    except Exception:  # noqa: BLE001 # any exception is fatal
        pytest.fail("Failed to connect to Yahoo! Finance API")

    assert yf._yclient._crumb

    symbols: list[str] = ["AAPL", "GOOG", "F"]
    quotes: list[YQuote] = await yf.retrieve_quotes(symbols)
    assert len(quotes) == len(symbols)

    for q in quotes:
        assert q.symbol in symbols
        symbols.remove(q.symbol)
