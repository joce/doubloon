"""Validate the behavior of the `YSearch` class."""

from __future__ import annotations

import zoneinfo
from datetime import date, datetime

import pytest

from calahan.enums import QuoteType
from tests.fake_yfinance import FakeYFinance


@pytest.mark.asyncio
async def test_ysearch_parses_quotes_section() -> None:
    """Ensure the YSearch model extracts quotes and converts fields appropriately."""

    search = await FakeYFinance().search("mortgage")

    assert search.count == 23
    assert len(search.quotes) == 7

    fannie = search.quotes[0]
    assert fannie.symbol == "FNMA"
    assert fannie.quote_type == QuoteType.EQUITY
    assert fannie.short_name == "Fannie Mae"
    assert fannie.score == 20546.0
    assert fannie.is_yahoo_finance is True

    freddie = next(q for q in search.quotes if q.symbol == "FMCC")
    assert freddie.quote_type == QuoteType.EQUITY
    assert freddie.long_name == "Federal Home Loan Mortgage Corporation"
    assert freddie.sector == "Financial Services"
    assert freddie.industry_disp == "Mortgage Finance"
    assert freddie.prev_name == "Freddie Mac"
    assert freddie.name_change_date == date(2025, 11, 8)


@pytest.mark.asyncio
async def test_ysearch_parses_news_and_nav_sections() -> None:
    """Ensure the YSearch model extracts news and nav sections when present."""

    result = await FakeYFinance().search("mortgage")

    assert len(result.news) == 10
    tzinfo = zoneinfo.ZoneInfo("America/New_York")

    lead_story = result.news[0]
    assert lead_story.uuid == "c1776a2e-bd29-3e9f-bdf4-eb50c3301d64"
    assert lead_story.provider_publish_time == datetime(
        2025, 11, 7, 23, 23, 26, tzinfo=tzinfo
    )
    assert lead_story.thumbnail is not None
    assert lead_story.thumbnail.resolutions[0].width == 1194

    housing_story = result.news[1]
    assert housing_story.related_tickers == [
        "PHM",
        "FMCC",
        "FMCCH",
        "FMCCK",
        "FMCCL",
        "FMCCO",
        "FMCCP",
        "FMCCT",
        "FMCKI",
        "FMCKJ",
        "FMCKL",
        "FMCKM",
        "FMCKN",
        "FMCKO",
        "FMCKP",
        "FREGP",
        "FREJN",
        "FNMA",
    ]

    assert len(result.nav) == 1
    nav_link = result.nav[0]
    assert nav_link.name == "Mortgages"
    assert nav_link.url == "https://finance.yahoo.com/personal-finance/mortgages/"


@pytest.mark.asyncio
async def test_ysearch_parses_lists_section() -> None:
    """Ensure the YSearch model extracts search lists with optional attributes."""

    result = await FakeYFinance().search("mortgage")

    assert len(result.lists) == 2

    mortgage_screen = result.lists[0]
    assert mortgage_screen.list_type == "PREDEFINED_SCREENER"
    assert mortgage_screen.title == "Mortgage Finance"
    assert mortgage_screen.canonical_name == "MORTGAGE_FINANCE"
    assert mortgage_screen.total == 8
    assert mortgage_screen.is_premium is False

    reit_screen = result.lists[1]
    assert reit_screen.list_type == "PREDEFINED_SCREENER"
    assert reit_screen.title == "REIT—Mortgage"
    assert reit_screen.canonical_name == "REIT_MORTGAGE"
    assert reit_screen.total == 87
    assert reit_screen.is_premium is False
