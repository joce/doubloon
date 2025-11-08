"""Validate the behavior of the `YSearch` class."""

# cspell:disable # noqa: ERA001
# ruff: noqa: PLR2004, E501

from __future__ import annotations

import zoneinfo
from datetime import date, datetime

from calahan import YSearchResult
from calahan.enums import QuoteType


def test_ysearch_parses_quotes_section() -> None:
    """Ensure the YSearch model extracts quotes and converts fields appropriately."""

    payload = {
        "count": 15,
        "quotes": [
            {
                "exchDisp": "Chicago Mercantile Exchange",
                "exchange": "CME",
                "index": "quotes",
                "isYahooFinance": "True",
                "quoteType": "FUTURE",
                "score": 30007.0,
                "shortname": "Bitcoin Futures,Oct-2025",
                "symbol": "BTC=F",
                "typeDisp": "Futures",
            },
            {
                "exchDisp": "NASDAQ",
                "exchange": "NCM",
                "index": "quotes",
                "industry": "Computer Hardware",
                "industryDisp": "Computer Hardware",
                "isYahooFinance": "True",
                "longname": "BTC Digital Ltd.",
                "nameChangeDate": "2025-11-01",
                "prevName": "Meten EdtechX Education Group Ltd.",
                "quoteType": "EQUITY",
                "score": 20029.0,
                "sector": "Technology",
                "sectorDisp": "Technology",
                "shortname": "BTC Digital Ltd.",
                "symbol": "BTCT",
                "typeDisp": "Equity",
            },
        ],
    }

    search = YSearchResult.model_validate(payload)

    assert search.count == 15
    assert len(search.quotes) == 2

    first_quote = search.quotes[0]
    assert first_quote.symbol == "BTC=F"
    assert first_quote.quote_type == QuoteType.FUTURE
    assert first_quote.short_name == "Bitcoin Futures,Oct-2025"
    assert first_quote.score == 30007.0
    assert first_quote.is_yahoo_finance is True

    equity_quote = search.quotes[1]
    assert equity_quote.quote_type == QuoteType.EQUITY
    assert equity_quote.long_name == "BTC Digital Ltd."
    assert equity_quote.sector == "Technology"
    assert equity_quote.industry_disp == "Computer Hardware"
    assert equity_quote.prev_name == "Meten EdtechX Education Group Ltd."
    assert equity_quote.name_change_date == date(2025, 11, 1)


def test_ysearch_parses_news_and_nav_sections() -> None:
    """Ensure the YSearch model extracts news and nav sections when present."""

    payload = {
        "count": 9,
        "quotes": [],
        "news": [
            {
                "uuid": "e2e4de9b-ab08-3382-a844-8ac63b502493",
                "title": "Tesla shareholder vote, Fed talk, mortgage rates: What to Watch",
                "publisher": "Yahoo Finance Video",
                "link": "https://finance.yahoo.com/video/tesla-shareholder-vote-fed-talk-000000603.html",
                "providerPublishTime": 1762387200,
                "type": "VIDEO",
                "thumbnail": {
                    "resolutions": [
                        {
                            "url": "https://s.yimg.com/uu/api/res/1.2/QTcLOVoblah2UCzS94ejvw--~B/aD0xMDgwO3c9MTkyMDthcHBpZD15dGFjaHlvbg--/https://s.yimg.com/os/creatr-uploaded-images/2025-11/e680b750-ba84-11f0-b6ff-e939105c5da2",
                            "width": 1920,
                            "height": 1080,
                            "tag": "original",
                        },
                        {
                            "url": "https://s.yimg.com/uu/api/res/1.2/FSpysiooJN8TOO.z_tlC9A--~B/Zmk9ZmlsbDtoPTE0MDtweW9mZj0wO3c9MTQwO2FwcGlkPXl0YWNoeW9u/https://s.yimg.com/os/creatr-uploaded-images/2025-11/e680b750-ba84-11f0-b6ff-e939105c5da2",
                            "width": 140,
                            "height": 140,
                            "tag": "140x140",
                        },
                    ]
                },
                "relatedTickers": [
                    "TSLA",
                    "AFRM",
                    "AZN",
                    "AZNCF",
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
                    "WBD",
                    "COP",
                    "AZN.L",
                    "ABNB",
                    "TTWO",
                ],
            },
            {
                "uuid": "2312a47d-e000-382b-83c2-5549b3eb77c4",
                "title": "KeyBank Provides $72.8 Million of Financing for New Affordable Senior Housing in Atlanta",
                "publisher": "ACCESS Newswire",
                "link": "https://finance.yahoo.com/news/keybank-provides-72-8-million-143000695.html",
                "providerPublishTime": 1762439400,
                "type": "STORY",
                "thumbnail": {
                    "resolutions": [
                        {
                            "url": "https://s.yimg.com/uu/api/res/1.2/Y1FdKMD81_o8HHZee2c1NQ--~B/aD00MDA7dz00MDA7YXBwaWQ9eXRhY2h5b24-/https://media.zenfs.com/en/accesswire.ca/bfce58f2dd92fe1c862656e5909e8190",
                            "width": 400,
                            "height": 400,
                            "tag": "original",
                        },
                        {
                            "url": "https://s.yimg.com/uu/api/res/1.2/_LcrNPu_PFUINOHQv9MBVQ--~B/Zmk9ZmlsbDtoPTE0MDtweW9mZj0wO3c9MTQwO2FwcGlkPXl0YWNoeW9u/https://media.zenfs.com/en/accesswire.ca/bfce58f2dd92fe1c862656e5909e8190",
                            "width": 140,
                            "height": 140,
                            "tag": "140x140",
                        },
                    ]
                },
                "relatedTickers": ["KEY", "FNMA"],
            },
        ],
        "nav": [
            {
                "navName": "Mortgages",
                "navUrl": "https://finance.yahoo.com/personal-finance/mortgages/",
            }
        ],
    }

    result = YSearchResult.model_validate(payload)

    assert len(result.news) == 2
    lead_story = result.news[0]
    assert lead_story.uuid == "e2e4de9b-ab08-3382-a844-8ac63b502493"
    assert lead_story.provider_publish_time == datetime.fromtimestamp(
        1762387200, tz=zoneinfo.ZoneInfo("America/New_York")
    )
    assert lead_story.thumbnail is not None
    assert lead_story.thumbnail.resolutions[0].width == 1920

    coindesk_story = result.news[1]
    assert coindesk_story.related_tickers == ["KEY", "FNMA"]

    assert len(result.nav) == 1
    nav_link = result.nav[0]
    assert nav_link.name == "Mortgages"
    assert nav_link.url == "https://finance.yahoo.com/personal-finance/mortgages/"


def test_ysearch_parses_lists_section() -> None:
    """Ensure the YSearch model extracts search lists with optional attributes."""

    payload = {
        "count": 9,
        "quotes": [],
        "news": [],
        "nav": [],
        "lists": [
            {
                "slug": "most-active-penny-stocks",
                "name": "Most Active Penny Stocks",
                "index": "most-active-penny-stocks",
                "score": 40.163948,
                "type": "ALGO_WATCHLIST",
                "brandSlug": "yahoo-finance",
                "pfId": "most_active_penny_stocks",
                "symbolCount": 30,
                "dailyPercentGain": 48.94833790508765,
                "followerCount": 63066,
                "iconUrl": "https://edgecast-img.yahoo.net/mysterio/api/26a4087f26113a9f01fdb35c900a7112eaa81d24d74f9ca80fd3615e7f26a360/finance/resizefill_w96_h96/https://s.yimg.com/cv/apiv2/fin/img/assets/watchlist/penny-stocks-top-gainers.jpg",
                "userId": "X3NJ2A7VDSABUI4URBWME2PZNM",
            },
            {
                "index": "05f97149-f902-4cd3-8f72-f7768ac673e0",
                "id": "05f97149-f902-4cd3-8f72-f7768ac673e0",
                "title": "Most Actives - France",
                "canonicalName": "MOST_ACTIVES_FR",
                "score": 1.0,
                "type": "PREDEFINED_SCREENER",
                "total": 8512,
                "isPremium": False,
                "iconUrl": "https://edgecast-img.yahoo.net/mysterio/api/f041b4d17c09d0aa6923ce2533c3d27f341dd1600e3f8325b72e09010c455a87/finance/resizefill_w96_h96/https://s.yimg.com/cv/apiv2/fin/img/assets/predefined_screeners/analytics.png",
            },
        ],
    }

    result = YSearchResult.model_validate(payload)

    assert len(result.lists) == 2

    watchlist = result.lists[0]
    assert watchlist.list_type == "ALGO_WATCHLIST"
    assert watchlist.slug == "most-active-penny-stocks"
    assert watchlist.brand_slug == "yahoo-finance"
    assert watchlist.symbol_count == 30
    assert watchlist.daily_percent_gain == 48.94833790508765
    assert watchlist.follower_count == 63066
    assert watchlist.user_id == "X3NJ2A7VDSABUI4URBWME2PZNM"

    screener = result.lists[1]
    assert screener.list_type == "PREDEFINED_SCREENER"
    assert screener.id == "05f97149-f902-4cd3-8f72-f7768ac673e0"
    assert screener.title == "Most Actives - France"
    assert screener.canonical_name == "MOST_ACTIVES_FR"
    assert screener.total == 8512
    assert screener.is_premium is False
