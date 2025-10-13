"""Async Yahoo! Finance API client."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Final

import httpx

if TYPE_CHECKING:
    from http.cookiejar import Cookie


class YAsyncClient:
    """Async Yahoo! Finance API client."""

    _YAHOO_FINANCE_URL: Final[str] = "https://finance.yahoo.com"
    _YAHOO_FINANCE_QUERY_URL: Final[str] = "https://query1.finance.yahoo.com"
    _CRUMB_URL: Final[str] = _YAHOO_FINANCE_QUERY_URL + "/v1/test/getcrumb"
    _ACCEPT_MIME_TYPES: Final[str] = (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;"
        "q=0.8,application/signed-exchange;v=b3;q=0.7"
    )
    _USER_AGENT: Final[str] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.3240.64"
    )
    _USER_AGENT_CLIENT_HINT_BRANDING_AND_VERSION: Final[str] = (
        '"Microsoft Edge";v="136", "Chromium";v="136", "Not;A=Brand";v="24"'
    )
    _USER_AGENT_CLIENT_HINT_PLATFORM: Final[str] = '"Windows"'
    _COOKIE_HEADERS: Final[dict[str, str]] = {
        "authority": "finance.yahoo.com",
        "accept": _ACCEPT_MIME_TYPES,
        "accept-language": "en-US,en;q=0.9",
        "upgrade-insecure-requests": "1",
        "user-agent": _USER_AGENT,
    }

    def __init__(self) -> None:
        self._timeout: httpx.Timeout = httpx.Timeout(
            connect=5, read=15, write=5, pool=5
        )
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            headers={
                "authority": "query1.finance.yahoo.com",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9,ja;q=0.8",
                "origin": self._YAHOO_FINANCE_URL,
                "user-agent": self._USER_AGENT,
            },
            timeout=self._timeout,
        )
        self._expiry: datetime = datetime(
            1970, 1, 1, tzinfo=datetime.now().astimezone().tzinfo
        )
        self._crumb: str = ""
        self._logger = logging.getLogger(__name__)
        self._refresh_lock = asyncio.Lock()

    async def _refresh_cookies(self) -> None:
        """Log into Yahoo! finance and set required cookies."""

        def _is_eu_consent_redirect(response: httpx.Response) -> bool:
            return (
                "guce.yahoo.com" in response.headers.get("Location", "")
                and response.is_redirect
            )

        self._logger.debug("Logging in...")

        response: httpx.Response | None = None
        try:
            response = await self._client.get(
                self._YAHOO_FINANCE_URL,
                headers=self._COOKIE_HEADERS,
                follow_redirects=False,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.is_error:
                self._logger.exception("Can't log in: %s", e.response)
                return
        except httpx.TransportError:
            self._logger.exception("Transport error logging in")
            return
        except asyncio.CancelledError:
            self._logger.exception("Cancelled log in")
            return

        cookies: httpx.Cookies = response.cookies if response else httpx.Cookies()

        if response and _is_eu_consent_redirect(response):
            cookies = await self._get_cookies_eu()

        if not any(cookie == "A3" for cookie in cookies):
            self._logger.error("Required cookie not set")
            return

        # Figure out how long the login is valid for.
        # Default expiry is ten years in the future
        expiry: datetime = datetime.now(timezone.utc).astimezone() + timedelta(
            days=3650
        )

        cookie: Cookie
        for cookie in cookies.jar:
            if cookie.domain != ".yahoo.com" or cookie.expires is None:
                continue
            cookie_expiry: datetime = datetime.fromtimestamp(
                cookie.expires, tz=datetime.now().astimezone().tzinfo
            )
            if cookie_expiry < expiry:
                self._logger.debug(
                    "Cookie %s accepted. Setting expiry to %s",
                    cookie.name,
                    cookie_expiry.strftime("%Y-%m-%d %H:%M:%S"),
                )
                expiry = cookie_expiry

        self._expiry = expiry
        # Invalidate the crumb, so it gets refreshed on next use
        self._crumb = ""

    async def _get_cookies_eu(self) -> httpx.Cookies:  # noqa: PLR0911 PLR0912
        """Get cookies from the EU consent page.

        Returns:
            httpx.Cookies: Cookies resulting from consent flow (may be empty).
        """

        result: httpx.Cookies = httpx.Cookies()
        response: httpx.Response | None = None
        session_id = None
        try:
            response = await self._client.get(
                self._YAHOO_FINANCE_URL,
                headers=self._COOKIE_HEADERS,
                follow_redirects=True,
            )
            response.raise_for_status()
            # Extract the session ID from the redirected request URL
            session_id = response.url.params.get("sessionId", "")
        except httpx.HTTPStatusError as e:
            if e.response.is_error:
                self._logger.exception(
                    "EU cookies initial request failed: %s", e.response
                )
                return result
        except httpx.TransportError:
            self._logger.exception("Transport error in initial request for EU cookies")
            return result
        except asyncio.CancelledError:
            self._logger.exception("Cancelled request for EU cookies")
            return result
        except (NameError, KeyError):
            self._logger.exception(
                "Unable to extract session id from redirected request URL: '%s'",
                self._YAHOO_FINANCE_URL,
            )
            return result

        if not session_id:
            self._logger.error("Session id missing in EU consent flow")
            return result

        # Find the right URL in the redirect history, and extract the CSRF token
        # from it
        guce_url: httpx.URL = httpx.URL("")
        for hist in response.history if response else []:
            if hist.url.host == "guce.yahoo.com":
                guce_url = hist.url
                break
        csrf_token = guce_url.params.get("gcrumb", "")
        if not csrf_token:
            self._logger.error("CSRF token missing in EU consent flow")
            return result

        # Look in the history to find the right cookie
        gucs_cookie: httpx.Cookies = httpx.Cookies()
        for hist in response.history if response else []:
            if hist.cookies.get("GUCS") is not None:
                gucs_cookie = hist.cookies
                break
        if len(gucs_cookie) == 0:
            self._logger.error("No GUCS cookie set by finance.yahoo.com")
            return result

        referrer_url = (
            "https://consent.yahoo.com/v2/collectConsent?sessionId=" + session_id
        )
        accept_mime_types = (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        )
        consent_headers: dict[str, str] = {
            "origin": "https://consent.yahoo.com",
            "host": "consent.yahoo.com",
            "content-type": "application/x-www-form-urlencoded",
            "accept": accept_mime_types,
            "accept-language": "en-US,en;q=0.5",
            "accept-encoding": "gzip, deflate, br",
            "dnt": "1",
            "referer": referrer_url,
            "user-agent": self._USER_AGENT,
        }
        data = {
            "csrfToken": csrf_token,
            "sessionId": session_id,
            "namespace": "yahoo",
            "agree": "agree",
        }
        try:
            response = await self._client.post(
                referrer_url,
                headers=consent_headers,
                cookies=gucs_cookie,
                data=data,
                follow_redirects=True,
            )
        except httpx.HTTPStatusError as e:
            self._logger.exception("Can't post consent: %s", e.response)
            return result
        except httpx.TransportError:
            self._logger.exception("Transport error posting consent")
            return result
        except asyncio.CancelledError:
            self._logger.exception("Cancelled posting consent")
            return result

        for hist in response.history if response else []:
            if hist.cookies.get("A3") is not None:
                result = hist.cookies
                break
        return result

    async def _refresh_crumb(self) -> None:
        """Refresh the crumb required to fetch quotes."""

        self._logger.debug("Refreshing crumb...")
        self._crumb = ""
        try:
            response: httpx.Response = await self._client.get(self._CRUMB_URL)
            response.raise_for_status()
            self._crumb = response.text
        except httpx.HTTPStatusError as e:
            self._logger.exception("Can't fetch crumb: %s", e.response)
        except httpx.TransportError:
            self._logger.exception("Transport error fetching crumb")
        except asyncio.CancelledError:
            self._logger.exception("Cancelled fetching crumb")

        if self._crumb:
            self._logger.debug(
                "Crumb refreshed: %s. Expires on %s",
                self._crumb,
                self._expiry.strftime("%Y-%m-%d %H:%M:%S"),
            )
        else:
            self._logger.debug("Crumb refresh failed")

    async def _ensure_ready(self) -> None:
        """Ensure cookies and crumb are valid (refresh if needed)."""

        # Fast path without lock
        now = datetime.now(timezone.utc).astimezone()
        if self._expiry >= now and self._crumb:
            return
        async with self._refresh_lock:
            now = datetime.now(timezone.utc).astimezone()
            if self._expiry < now:
                await self._refresh_cookies()
            if not self._crumb:
                await self._refresh_crumb()

    async def _execute_api_call(
        self, api_call: str, query_params: dict[str, str]
    ) -> dict[str, Any]:
        """Execute the given api call with the given params and return parsed JSON.

        Args:
            api_call (str): API endpoint (e.g. '/v10/finance/quoteSummary/MSFT').

            query_params (dict[str, str]): Query parameters to include.

        Returns:
            dict[str, Any]: Parsed JSON response or empty dict on failure.
        """

        self._logger.debug("Executing request: %s", api_call)
        try:
            response: httpx.Response = await self._client.get(
                self._YAHOO_FINANCE_QUERY_URL + api_call, params=query_params
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._logger.exception("Call to api failed: %s", e.response)
            return {}
        except httpx.TransportError:
            self._logger.exception("Transport error executing api call")
            return {}
        except asyncio.CancelledError:
            self._logger.exception("Cancelled api call")
            return {}

        res_body: str = response.text
        self._logger.debug("Response: %s", res_body)
        if not res_body:
            self._logger.error("Can't parse response")
            return {}
        try:
            return json.loads(res_body)
        except json.JSONDecodeError:
            self._logger.exception("JSON decode failed")
            return {}

    async def prime(self) -> None:
        """Prime the client (refresh cookies then crumb)."""
        await self._ensure_ready()

    async def call(
        self, api_url: str, query_params: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Execute Yahoo! Finance API call asynchronously.

        Args:
            api_url (str): API endpoint (e.g. '/v10/finance/quoteSummary/MSFT').

            query_params (dict[str, str] | None): Query parameters to include
                (excluding 'crumb' which is added automatically).

        Returns:
            dict[str, Any]: JSON response (empty dict on error).
        """

        self._logger.debug("Calling %s with params %s", api_url, query_params)

        await self._ensure_ready()

        if query_params is None:
            query_params = {}
        if self._crumb:
            query_params["crumb"] = self._crumb
        return await self._execute_api_call(api_url, query_params)

    async def aclose(self) -> None:
        """Close the underlying AsyncClient."""
        await self._client.aclose()
