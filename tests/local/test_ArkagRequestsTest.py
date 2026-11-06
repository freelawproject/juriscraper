"""Date-boundary and audited HTTP regressions for Arkansas's search API."""

import asyncio
import json
from datetime import date

import httpx
import pytest

from juriscraper.lib.exceptions import ParsingException
from juriscraper.opinions.united_states.attorney_general.arkag import Site

HOST = "https://example.meilisearch.io"
KEY = "public-search-fixture-key-123456"


def discovery_response(request):
    assert "authorization" not in request.headers
    assert not request.content
    assert not request.url.query
    if request.url.path == "/":
        return httpx.Response(
            200, text='<script src="/assets/index.js"></script>'
        )
    return httpx.Response(200, text=f'"{HOST}","{KEY}"')


def test_repeated_intervals_audit_discovery_without_search_state():
    async def run():
        posts = []
        audited = []

        def handler(request):
            if request.method == "GET":
                return discovery_response(request)
            payload = json.loads(request.content)
            posts.append(payload)
            assert request.headers["authorization"] == f"Bearer {KEY}"
            assert payload["limit"] == 1000
            assert "OpenFileNo STARTS WITH" not in payload["filter"]
            return httpx.Response(
                200, json={"hits": [], "estimatedTotalHits": 0}
            )

        site = Site(transport=httpx.MockTransport(handler))
        headers = site.request["headers"]
        parameters = site.request["parameters"]
        site.save_response = lambda scraper: audited.append(
            (scraper.request["url"], scraper.request["response"].status_code)
        )
        async with site.request["session"]:
            await site._download_backwards(
                (date(2026, 10, 20), date(2026, 10, 28))
            )
            await site._download_backwards(
                (date(2026, 10, 29), date(2026, 10, 29))
            )
        assert posts[0]["filter"] == (
            'Date_Published >= "2026-10-20" AND Date_Published < "2026-10-29"'
        )
        assert posts[1]["filter"] == (
            'Date_Published >= "2026-10-29" AND Date_Published < "2026-10-30"'
        )
        assert [url for url, _ in audited] == [
            Site.home_url,
            Site.home_url + "assets/index.js",
            HOST + "/indexes/opinions/search",
        ] * 2
        assert site.method == "GET"
        assert site.request["headers"] is headers
        assert site.request["parameters"] is parameters
        assert parameters == {}
        assert "Authorization" not in headers

    asyncio.run(run())


@pytest.mark.parametrize("status", [200, 503])
def test_discovery_strips_stale_json_and_authorization_and_restores_on_error(
    status,
):
    async def run():
        def handler(request):
            assert "authorization" not in request.headers
            assert "content-type" not in request.headers
            assert not request.content
            assert not request.url.query
            return httpx.Response(status, text="bundle")

        site = Site(transport=httpx.MockTransport(handler))
        site.request["headers"].update(
            {"authorization": "Bearer stale", "Accept": "application/json"}
        )
        site.request["parameters"] = {
            "json": {"filter": "stale"},
            "params": {"offset": 1000},
        }
        headers, parameters = (
            site.request["headers"],
            site.request["parameters"],
        )
        audited = []
        site.save_response = lambda scraper: audited.append(
            scraper.request["response"].status_code
        )
        async with site.request["session"]:
            if status == 200:
                assert await site._fetch_text(Site.home_url) == "bundle"
            else:
                with pytest.raises(httpx.HTTPStatusError):
                    await site._fetch_text(Site.home_url)
        assert audited == [status]
        assert site.request["headers"] is headers
        assert site.request["parameters"] is parameters

    asyncio.run(run())


@pytest.mark.parametrize(
    "response",
    [
        {"hits": [{}], "estimatedTotalHits": 2},
        {"hits": [{}] * 1000, "estimatedTotalHits": 1000},
    ],
)
def test_backfill_refuses_partial_or_capped_results(response):
    async def run():
        def handler(request):
            if request.method == "GET":
                return discovery_response(request)
            return httpx.Response(200, json=response)

        site = Site(transport=httpx.MockTransport(handler))
        async with site.request["session"]:
            with pytest.raises(ParsingException, match="reduce days_interval"):
                await site._download_backwards(
                    (date(2012, 1, 1), date(2026, 11, 6))
                )
        assert site.cases == []
        assert site.request["parameters"] == {}
        assert "Authorization" not in site.request["headers"]

    asyncio.run(run())


def test_publication_date_can_include_an_earlier_docket_year():
    # Real boundary example: the source publishes 2011-159 on 2012-04-03.
    # https://opinionstorage.blob.core.windows.net/opinions/2011-159.pdf
    async def run():
        def handler(request):
            if request.method == "GET":
                return discovery_response(request)
            payload = json.loads(request.content)
            assert payload["filter"] == (
                'Date_Published >= "2012-04-03" AND Date_Published < "2012-04-04"'
            )
            return httpx.Response(
                200,
                json={
                    "estimatedTotalHits": 1,
                    "hits": [
                        {
                            "OpenFileNo": "2011-159",
                            "Date_Published": "2012-04-03T00:00:00.0000000",
                            "RequestorNameFull": "Requester",
                            "OpinionSummary": "Fixture summary.",
                            "PDFUrl": "https://opinionstorage.blob.core.windows.net/opinions/2011-159.pdf",
                        }
                    ],
                },
            )

        site = Site(transport=httpx.MockTransport(handler))
        async with site.request["session"]:
            await site._download_backwards(
                (date(2012, 4, 3), date(2012, 4, 3))
            )
        assert len(site.cases) == 1
        assert site.cases[0]["docket"] == "2011-159"
        assert site.cases[0]["date"] == "2012-04-03"

    asyncio.run(run())
