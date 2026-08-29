"""Tests for the ca9 DynamoDB scan pagination.

The example file tests feed `_process_html` a ready made list of rows, so they
never reach `_download`. These swap the site's client for an
``httpx.MockTransport`` to exercise the Scan pagination loop itself, following
the strategy used in the Florida scraper tests.
"""

from __future__ import annotations

import json
import unittest

import httpx

from juriscraper.opinions.united_states.federal_appellate import ca9_p

CREDENTIALS = {
    "Credentials": {
        "AccessKeyId": "fake-access-key-id",
        "SecretKey": "fake-secret-key",
        "SessionToken": "fake-session-token",
    }
}


def make_row(docket: str) -> dict:
    """Build the smallest row `_process_html` will accept

    :param docket: the case number to put on the row
    :return: a DynamoDB row
    """
    return {
        "case_name": {"S": f"CASE {docket}"},
        "case_num": {"S": docket},
        "deleted": {"S": "0"},
        "file_name": {"S": f"/datastore/opinions/2026/06/01/{docket}.pdf"},
        "last_updated": {"S": "2026-06-01 09:00:00"},
        "publish": {"N": "20260601000000"},
    }


class CA9PaginationTest(unittest.IsolatedAsyncioTestCase):
    def make_site(self, pages: list[dict]) -> tuple[ca9_p.Site, list[dict]]:
        """Build a site whose client replays `pages` for each Scan

        :param pages: the Scan response bodies to return, in order
        :return: the site, and the list that collects the sent scan payloads
        """
        site = ca9_p.Site()
        sent_payloads: list[dict] = []
        remaining = list(pages)

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host.startswith("cognito"):
                return httpx.Response(200, json=CREDENTIALS)

            sent_payloads.append(json.loads(request.content))
            return httpx.Response(
                200,
                content=json.dumps(remaining.pop(0)),
                headers={"content-type": "application/x-amz-json-1.0"},
            )

        site.request["session"] = httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        )
        return site, sent_payloads

    async def test_follows_last_evaluated_key(self) -> None:
        """Every page is collected and the cursor is fed back to the court"""
        pages = [
            {
                "Items": [make_row("25-1000")],
                "LastEvaluatedKey": {"pk_id": {"S": "1"}},
            },
            {
                "Items": [make_row("25-1001")],
                "LastEvaluatedKey": {"pk_id": {"S": "2"}},
            },
            {"Items": [make_row("25-1002")]},
        ]
        site, sent_payloads = self.make_site(pages)

        async with site.request["session"]:
            items = await site._download()

        self.assertEqual(len(items), 3)
        self.assertEqual(len(sent_payloads), 3)
        # The first scan starts at the top of the table; each later scan
        # resumes from the key the previous page returned
        self.assertNotIn("ExclusiveStartKey", sent_payloads[0])
        self.assertEqual(
            sent_payloads[1]["ExclusiveStartKey"], {"pk_id": {"S": "1"}}
        )
        self.assertEqual(
            sent_payloads[2]["ExclusiveStartKey"], {"pk_id": {"S": "2"}}
        )

    async def test_stops_at_max_pages(self) -> None:
        """A table that never stops paginating cannot loop forever"""
        pages = [
            {
                "Items": [make_row(f"25-100{i}")],
                "LastEvaluatedKey": {"pk_id": {"S": str(i)}},
            }
            for i in range(5)
        ]
        site, sent_payloads = self.make_site(pages)
        site.max_pages = 3

        with self.assertLogs("juriscraper", level="ERROR") as logs:
            async with site.request["session"]:
                items = await site._download()

        self.assertEqual(len(items), 3)
        self.assertEqual(len(sent_payloads), 3)
        self.assertIn("page scan limit", logs.output[0])

    async def test_single_page_scan(self) -> None:
        """A scan that fits in one response sends a single request"""
        site, sent_payloads = self.make_site(
            [{"Items": [make_row("25-1000"), make_row("25-1001")]}]
        )

        async with site.request["session"]:
            items = await site._download()

        self.assertEqual(len(items), 2)
        self.assertEqual(len(sent_payloads), 1)


if __name__ == "__main__":
    unittest.main()
