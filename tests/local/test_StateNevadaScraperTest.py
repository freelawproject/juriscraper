import copy
import json
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.state import (
    nev,
    nev_u,
    nevapp,
    nevapp_u,
)


class NevadaScraperTest(unittest.IsolatedAsyncioTestCase):
    examples = Path("tests/examples/opinions/united_states")

    def make_site(self, module):
        site = module.Site()
        self.addAsyncCleanup(site.request["session"].aclose)
        return site

    async def test_nevada_fixtures(self):
        for module in (nev, nevapp, nev_u, nevapp_u):
            name = module.__name__.rsplit(".", 1)[-1]
            with self.subTest(scraper=name):
                site = self.make_site(module)
                site.mock_url = str(self.examples / f"{name}_example.json")
                site.enable_test_mode()
                await site.parse()
                expected = json.loads(
                    (
                        self.examples / f"{name}_example.compare.json"
                    ).read_text()
                )
                self.assertEqual(json.loads(site.to_json()), expected)

    async def test_unpublished_supreme_court_metadata(self):
        site = self.make_site(nev_u)
        metadata = site.parse_description(
            'Filed Order of Affirmance. "ORDER the judgment AFFIRMED." '
            "Majority: KP/RP/LB",
            "2026-07-08",
        )
        self.assertEqual(metadata["disposition"], "Order of Affirmance")
        self.assertEqual(metadata["citation"], "")
        self.assertEqual(
            metadata["judge"],
            "Kristina Pickering, Ron D. Parraguirre, Linda Marie Bell",
        )
        self.assertEqual(site.status, "Unpublished")

    async def test_unpublished_appeals_judges_by_filed_date(self):
        site = self.make_site(nevapp_u)
        for filed, panel, judges in (
            (
                "2026-07-08",
                "BB/MG/DW",
                "Bonnie A. Bulla, Michael P. Gibbons, Deborah L. Westbrook",
            ),
            (
                "2018-07-08",
                "AS/MG/JT",
                "Abbi Silver, Michael P. Gibbons, Jerome T. Tao",
            ),
        ):
            with self.subTest(date=filed):
                metadata = site.parse_description(
                    f"Order of Affirmance. Majority: {panel}", filed
                )
                self.assertEqual(metadata["judge"], judges)
        self.assertEqual(site.court_id, nevapp_u.__name__)
        self.assertEqual(site.status, "Unpublished")

    async def test_unknown_judges_still_log_during_regular_scrapes(self):
        for module in (nev, nevapp, nev_u, nevapp_u):
            with self.subTest(scraper=module.__name__):
                site = self.make_site(module)
                with self.assertLogs(logger, level="ERROR") as logs:
                    self.assertEqual(
                        site.resolve_initials("ZZ", "2026-07-08"), ""
                    )
                self.assertIn("ZZ on 2026-07-08", logs.output[0])

    async def test_backscrape_keeps_known_judges_without_unknown_errors(self):
        for module, prefix, panel, judges in (
            (
                nev_u,
                "nev_u",
                "ZZ/JH",
                "James W. Hardesty",
            ),
            (
                nevapp_u,
                "nevapp_u",
                "ZZ/MG",
                "Michael P. Gibbons",
            ),
        ):
            with self.subTest(scraper=module.__name__):
                site = self.make_site(module)
                fixture = json.loads(
                    (self.examples / f"{prefix}_example.json").read_text()
                )
                result = copy.deepcopy(fixture["_embedded"]["results"][0])
                result["docketEntryHeader"].update(
                    filedDate="2018-07-08T15:36:13.000+00:00",
                    docketEntryDescription=(
                        f"Filed Order of Affirmance. Majority: {panel}"
                    ),
                )
                with (
                    patch.object(
                        site,
                        "_download",
                        new=AsyncMock(
                            side_effect=[
                                {"_embedded": {"results": [result]}},
                                {},
                            ]
                        ),
                    ),
                    self.assertNoLogs(logger, level="ERROR"),
                ):
                    await site._download_backwards(
                        (date(2018, 7, 1), date(2018, 7, 31))
                    )
                self.assertEqual(len(site.cases), 1)
                self.assertEqual(site.cases[0]["judge"], judges)
                self.assertEqual(
                    site.cases[0]["disposition"], "Order of Affirmance"
                )
