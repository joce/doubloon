"""Calahan-specific exception hierarchy."""

from __future__ import annotations


class CalahanError(Exception):
    """Base exception for all Calahan errors."""

    def __init__(self, message: str) -> None:
        """Initialize the error.

        Args:
            message (str): Human-readable error message.
        """

        super().__init__(message)


class MarketDataUnavailableError(CalahanError):
    """Raised when market data cannot be retrieved due to transport issues."""

    def __init__(self, context: str) -> None:
        """Initialize the error.

        Args:
            context (str): Description of the action being attempted.
        """

        message = f"Market data unavailable for {context}"
        super().__init__(message)
        self.context = context


class MarketDataRequestError(CalahanError):
    """Raised when Yahoo rejects the market data request."""

    def __init__(
        self,
        status_code: int,
        url: str,
        *,
        reason: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            status_code (int): HTTP status returned by Yahoo.
            url (str): Request URL that was rejected.
            reason (str | None): Optional additional reason for the rejection.
        """

        message = f"Market data request rejected with HTTP {status_code} for {url}"
        if reason:
            message = f"{message}: {reason}"
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.reason = reason


class MarketDataMalformedError(CalahanError):
    """Raised when market data cannot be parsed or validated."""

    def __init__(self, context: str) -> None:
        """Initialize the error.

        Args:
            context (str): Identifier for the data being parsed.
        """

        message = f"Received malformed market data while processing {context}"
        super().__init__(message)
        self.context = context
