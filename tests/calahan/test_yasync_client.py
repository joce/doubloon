"""Unit tests for the YAsyncClient helper."""

# pyright: reportPrivateUsage=none
# pyright: reportAttributeAccessIssue=none

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from http.cookiejar import Cookie
from typing import TYPE_CHECKING, Final
from unittest.mock import AsyncMock

import httpx
import pytest
from freezegun import freeze_time

if TYPE_CHECKING:
    from pytest_httpx import HTTPXMock

from calahan._yasync_client import YAsyncClient
from calahan.exceptions import (
    ConsentFlowFailedError,
    MarketDataRequestError,
    MarketDataUnavailableError,
)

###################################
# _ensure_ready Tests
###################################


@pytest.mark.asyncio
@freeze_time("2025-10-10 12:00:00")
async def test_ensure_ready_does_not_refresh_when_not_needed() -> None:
    """Test that ensure_ready doesn't refresh when not expired and crumb valid."""

    client = YAsyncClient()
    client._crumb = "valid_crumb"

    # Client cookies expire in 5 minutes
    client._expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
    client._refresh_cookies = AsyncMock()
    client._refresh_crumb = AsyncMock()

    await client._ensure_ready()

    assert not client._refresh_cookies.called
    assert not client._refresh_crumb.called


@pytest.mark.asyncio
@freeze_time("2025-10-10 12:00:00")
async def test_ensure_ready_refreshes_cookies_when_expired() -> None:
    """Test that ensure_ready refreshes cookies when expired."""

    client = YAsyncClient()
    client._crumb = "valid_crumb"

    # Client cookies expired 5 minutes ago
    client._expiry = datetime.now(timezone.utc) + timedelta(minutes=-5)
    client._refresh_cookies = AsyncMock()
    client._refresh_crumb = AsyncMock()

    await client._ensure_ready()

    assert client._refresh_cookies.called
    assert not client._refresh_crumb.called


@pytest.mark.asyncio
@freeze_time("2025-10-10 12:00:00")
async def test_ensure_ready_refreshes_crumbs_when_expired() -> None:
    """Test that ensure_ready refreshes cookies when expired."""

    client = YAsyncClient()

    # Crumb is missing
    client._crumb = ""

    # Client cookies expire in 5 minutes
    client._expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
    client._refresh_cookies = AsyncMock()
    client._refresh_crumb = AsyncMock()

    await client._ensure_ready()

    assert not client._refresh_cookies.called
    assert client._refresh_crumb.called


###################################
# _safe_request Tests
###################################

EXAMPLE_URL = "https://example.com"


@pytest.mark.asyncio
async def test_safe_request_get_success(httpx_mock: HTTPXMock) -> None:
    """Return response when _safe_request succeeds."""

    httpx_mock.add_response(url=EXAMPLE_URL, status_code=200)

    client = YAsyncClient()
    response = await client._request_or_raise("GET", EXAMPLE_URL, context="ctx")

    assert response is not None
    assert response.status_code == httpx.codes(200)

    # Verify the request was made
    request = httpx_mock.get_request()
    assert request is not None
    assert request.url == EXAMPLE_URL
    assert request.method == "GET"


@pytest.mark.asyncio
async def test_safe_request_handles_http_status_error(
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Raise MarketDataRejected when HTTP status error occurs."""

    httpx_mock.add_response(url=EXAMPLE_URL, status_code=404)

    client = YAsyncClient()
    with caplog.at_level("ERROR"), pytest.raises(MarketDataRequestError):
        await client._request_or_raise("GET", EXAMPLE_URL, context="ctx")

    assert "HTTP error for 'ctx': Status 404" in caplog.text

    request = httpx_mock.get_request()
    assert request is not None


@pytest.mark.asyncio
async def test_safe_request_handles_transport_error(
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Raise MarketDataUnavailable on transport error."""

    httpx_mock.add_exception(httpx.TransportError("fail"), url=EXAMPLE_URL)

    client = YAsyncClient()
    with caplog.at_level("ERROR"), pytest.raises(MarketDataUnavailableError):
        await client._request_or_raise("GET", EXAMPLE_URL, context="ctx")

    assert "Transport error for 'ctx'" in caplog.text


@pytest.mark.asyncio
async def test_safe_request_handles_cancelled_error(
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Handle cancelled requests gracefully."""

    httpx_mock.add_exception(
        asyncio.CancelledError(), url=EXAMPLE_URL  # type: ignore ReportArgumentType
    )

    client = YAsyncClient()
    with caplog.at_level("INFO"), pytest.raises(asyncio.CancelledError):
        await client._request_or_raise("GET", EXAMPLE_URL, context="ctx")

    assert "Request cancelled for 'ctx'" in caplog.text


##############################
#  cookies refresh tests
##############################


@pytest.mark.asyncio
async def test_refresh_cookies_no_response(
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Raise ConsentFlowFailed when login request fails."""

    # Simulate internal server error during login
    httpx_mock.add_response(url=YAsyncClient._YAHOO_FINANCE_URL, status_code=500)

    client = YAsyncClient()

    with caplog.at_level("ERROR"), pytest.raises(ConsentFlowFailedError):
        await client._refresh_cookies()

    assert "Cookie refresh failed" in caplog.text


@pytest.mark.asyncio
async def test_refresh_cookies_missing_a3_cookie(
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Raise ConsentFlowFailed when Yahoo login does not issue the req'd A3 cookie."""

    httpx_mock.add_response(
        url=YAsyncClient._YAHOO_FINANCE_URL,
        status_code=200,
        headers={"Set-Cookie": "OTHER=value; Domain=.yahoo.com; Path=/"},
    )

    client = YAsyncClient()

    with caplog.at_level("ERROR"), pytest.raises(ConsentFlowFailedError):
        await client._refresh_cookies()

    assert "Required A3 cookie not set" in caplog.text


def test_extract_session_id_returns_value() -> None:
    """Session ID is returned when present in the redirect URL."""

    client = YAsyncClient()
    response = httpx.Response(
        status_code=302,
        request=httpx.Request("GET", "https://guce.yahoo.com/consent?sessionId=abc123"),
    )

    session_id = client._extract_session_id(response)

    assert session_id == "abc123"


def test_extract_session_id_missing_logs_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing sessionId parameter logs an error and raises."""

    client = YAsyncClient()
    response = httpx.Response(
        status_code=302,
        request=httpx.Request("GET", "https://guce.yahoo.com/consent"),
    )

    with caplog.at_level("ERROR"), pytest.raises(ConsentFlowFailedError):
        client._extract_session_id(response)

    assert "Session ID missing from redirect URL" in caplog.text


def test_extract_csrf_token_returns_value() -> None:
    """Extract CSRF token from guce redirect history."""

    crumb = "crumb123"
    client = YAsyncClient()
    guce_response = httpx.Response(
        status_code=302,
        request=httpx.Request(
            "GET",
            f"https://guce.yahoo.com/consent?gcrumb={crumb}",
        ),
    )
    other_response = httpx.Response(
        status_code=302,
        request=httpx.Request(
            "GET",
            "https://example.com/another",
        ),
    )
    response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://example.com/final"),
        history=[other_response, guce_response],
    )

    csrf_token = client._extract_csrf_token(response)

    assert csrf_token == crumb


def test_extract_csrf_token_missing_logs_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Log error and raise when gcrumb missing in history."""

    client = YAsyncClient()
    redirect_response = httpx.Response(
        status_code=302,
        request=httpx.Request("GET", "https://example.com/redirect"),
    )
    guce_response = httpx.Response(
        status_code=302,
        request=httpx.Request("GET", "https://guce.yahoo.com/consent"),
    )
    response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://example.com/final"),
        history=[redirect_response, guce_response],
    )

    with caplog.at_level("ERROR"), pytest.raises(ConsentFlowFailedError):
        client._extract_csrf_token(response)

    assert "CSRF token missing" in caplog.text
    assert "example.com" in caplog.text


def test_extract_gucs_cookie_returns_cookie() -> None:
    """Extract GUCS cookie from redirect history."""

    client = YAsyncClient()
    guce_response = httpx.Response(
        status_code=302,
        request=httpx.Request("GET", "https://guce.yahoo.com/consent"),
    )
    guce_response.cookies.set("GUCS", "cookie_value")
    other_response = httpx.Response(
        status_code=302,
        request=httpx.Request("GET", "https://example.com/next"),
    )
    other_response.cookies.set("OTHER", "value")
    response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://example.com/final"),
        history=[other_response, guce_response],
    )

    cookies = client._extract_gucs_cookie(response)

    assert cookies is not None
    assert cookies.get("GUCS") == "cookie_value"


def test_extract_gucs_cookie_missing_logs_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Log error and raise when GUCS cookie missing."""

    client = YAsyncClient()
    redirect_response = httpx.Response(
        status_code=302,
        request=httpx.Request("GET", "https://example.com/redirect"),
    )
    redirect_response.cookies.set("OTHER", "value")
    guce_response = httpx.Response(
        status_code=302,
        request=httpx.Request("GET", "https://guce.yahoo.com/consent"),
    )
    response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://example.com/final"),
        history=[redirect_response, guce_response],
    )

    with caplog.at_level("ERROR"), pytest.raises(ConsentFlowFailedError):
        client._extract_gucs_cookie(response)

    assert "GUCS cookie not set" in caplog.text


##############################
#  expiry refresh tests
##############################

CookieSpec = tuple[str, str, timedelta | None]
TEN_YEAR_OFFSET: Final[timedelta] = timedelta(days=365 * 10)


@pytest.mark.parametrize(
    ("cookie_specs", "expected_offset"),
    [
        pytest.param([], TEN_YEAR_OFFSET, id="no-cookies"),
        pytest.param(
            [("A3", "example.com", timedelta(days=365))],
            TEN_YEAR_OFFSET,
            id="non-yahoo-domain",
        ),
        pytest.param(
            [("A3", ".yahoo.com", None)],
            TEN_YEAR_OFFSET,
            id="yahoo-missing-expiry",
        ),
        pytest.param(
            [("A3", ".yahoo.com", timedelta(days=365))],
            timedelta(days=365),
            id="yahoo-with-expiry",
        ),
    ],
)
@freeze_time("2025-10-10 12:00:00")
def test_refresh_expiry_updates_expiry_and_invalidates_crumb(
    cookie_specs: list[CookieSpec],
    expected_offset: timedelta,
) -> None:
    """Ensure _refresh_expiry picks earliest valid expiry and clears crumb."""

    def _build_cookie(name: str, domain: str, expires: datetime | None) -> Cookie:
        return Cookie(
            version=0,
            name=name,
            value="value",
            port=None,
            port_specified=False,
            domain=domain,
            domain_specified=True,
            domain_initial_dot=domain.startswith("."),
            path="/",
            path_specified=True,
            secure=False,
            expires=int(expires.timestamp()) if expires else None,
            discard=False,
            comment=None,
            comment_url=None,
            rest={},
        )

    client = YAsyncClient()
    client._crumb = "existing"

    base_now = datetime.now(timezone.utc).astimezone()
    cookies = httpx.Cookies()

    for name, domain, expires_offset in cookie_specs:
        if expires_offset is not None:
            expires_dt = base_now + expires_offset
            cookie = _build_cookie(name, domain, expires_dt)
        else:
            cookie = _build_cookie(name, domain, None)
        cookies.jar.set_cookie(cookie)

    client._refresh_expiry(cookies)

    expected_expiry = base_now + expected_offset
    assert client._expiry == expected_expiry
    assert not client._crumb
