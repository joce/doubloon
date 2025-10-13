"""Synchronous facade for YAsyncClient."""

from __future__ import annotations

import asyncio
import contextlib
import sys
import threading
from typing import TYPE_CHECKING, Any, TypeVar

from ._yasync_client import YAsyncClient

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from types import TracebackType

T = TypeVar("T")


class YSyncClient:
    """Threaded event-loop based sync facade for YAsyncClient.

    Usage:
        client = YSyncClient()
        data = client.call("/v10/finance/quoteSummary/MSFT",
                           {"modules": "price,summaryDetail"})
        client.close()

    Safe for repeated calls from one thread. Not re-entrant across multiple
    threads (add your own locking if needed).
    """

    def __init__(self) -> None:
        self._ayc = YAsyncClient()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, name="YSyncClientLoop", daemon=True
        )
        self._thread.start()

    def _run_loop(self) -> None:
        """Run the event loop in a background thread."""

        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run(self, coroutine: Coroutine[Any, Any, T]) -> T:
        """Submit coroutine to background loop and wait for result.

        Args:
            coroutine (Coroutine): Coroutine to run.

        Returns:
            Any: Result of the coroutine.
        """
        fut = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        return fut.result()

    def prime(self) -> None:
        """Ensure cookies + crumb are ready."""
        self._run(self._ayc.prime())

    def call(
        self, api_url: str, query_params: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Execute a Yahoo! Finance API call synchronously.

        Args:
            api_url (str): API endpoint (e.g. '/v10/finance/quoteSummary/MSFT').
            query_params (dict[str, str] | None): Query parameters as key-value
                pairs.

        Returns:
            dict[str, Any]: Parsed JSON response from the API.
        """
        return self._run(self._ayc.call(api_url, query_params))

    def close(self) -> None:
        """Close underlying async client and stop loop."""
        # Idempotent
        if not self._loop.is_running():
            return
        try:
            self._run(self._ayc.aclose())
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=2)
            self._loop.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.close()
