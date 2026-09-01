#!/usr/bin/env python
"""Guards the ordering contract that CourtListener's crawl abort depends on.

CourtListener walks a scraped list from the top and stops at the first
document it already has. That is only safe on a list that runs newest first,
by publication time. A scraper states whether it delivers that with
`AbstractSite.is_recency_ordered`, and orders by a source publication time by
giving each case a `sort_key`. See #2152.
"""

import glob
import json
import logging
import os
import unittest
from collections import Counter

from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.importer import build_module_list
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

PACKAGES = ("juriscraper.opinions", "juriscraper.oral_args")

# Two cases filed the same day, plus an older one. The court published the
# second case first, so `upload` disagrees with the case name tiebreak that
# `_date_sort` would otherwise fall back on.
CASES = [
    {
        "name": "Alpha v. State",
        "url": "https://court.gov/alpha.pdf",
        "date": "2026-08-25",
        "docket": "A-1",
        "upload": "2026-08-25 11:21:00",
    },
    {
        "name": "Beta v. State",
        "url": "https://court.gov/beta.pdf",
        "date": "2026-08-25",
        "docket": "B-2",
        "upload": "2026-08-25 07:16:00",
    },
    {
        "name": "Gamma v. State",
        "url": "https://court.gov/gamma.pdf",
        "date": "2026-08-24",
        "docket": "C-3",
        "upload": "2026-08-24 09:00:00",
    },
]


def build_cases(with_sort_key: bool = True) -> list[dict]:
    """Copy the sample cases, moving `upload` into `sort_key` or dropping it

    :param with_sort_key: order by the upload time rather than filing date
    :return: fresh case dicts, safe to mutate
    """
    cases = []
    for case in CASES:
        case = dict(case)
        upload = case.pop("upload")
        if with_sort_key:
            case["sort_key"] = upload
        cases.append(case)
    return cases


class FakeSite(OpinionSiteLinear):
    """A scraper whose cases are handed in, so no download is needed"""

    def __init__(self, cases, **kwargs):
        super().__init__(**kwargs)
        self.court_id = "fake"
        self.status = "Published"
        self.cases = cases
        # skips `_download` and `_process_html` in `parse`
        self.downloader_executed = True


def example_paths(module_string: str) -> list[str]:
    """Find the example files of a scraper module

    :param module_string: full dotted path of the scraper
    :return: paths of its example files, without the compare files
    """
    parts = module_string.split(".")
    pattern = os.path.join(
        "tests", "examples", parts[1], "united_states", f"{parts[-1]}_example*"
    )
    return [
        path
        for path in sorted(glob.glob(pattern))
        if not path.endswith(".compare.json") and not path.endswith("~")
    ]


def scraper_modules() -> list[str]:
    """List every scraper module, minus the backscraper variants

    :return: full dotted paths of the scraper modules
    """
    modules = []
    for package in PACKAGES:
        modules.extend(
            module
            for module in build_module_list(package)
            if "backscraper" not in module
        )
    return modules


class SortKeyTest(unittest.IsolatedAsyncioTestCase):
    """The `sort_key` hook itself"""

    async def test_sort_key_sets_the_order(self):
        """A `sort_key` orders the list, over the filing date"""
        site = await FakeSite(build_cases()).parse()

        # Beta uploaded before Alpha, so Alpha leads even though its name
        # sorts first and both share a filing date
        self.assertEqual(
            list(site.case_names),
            ["Alpha v. State", "Beta v. State", "Gamma v. State"],
        )

    async def test_reverse_sort_key_reverses_the_order(self):
        """The order follows the key, it is not a filing date sort in disguise"""
        cases = build_cases()
        # Beta now uploaded last, so it must lead
        cases[1]["sort_key"] = "2026-08-25 23:59:00"
        site = await FakeSite(cases).parse()

        self.assertEqual(
            list(site.case_names),
            ["Beta v. State", "Alpha v. State", "Gamma v. State"],
        )

    async def test_without_a_sort_key_the_date_sort_is_unchanged(self):
        """Scrapers that set no `sort_key` keep the filing date behaviour"""
        site = await FakeSite(build_cases(with_sort_key=False)).parse()

        # same date, so the tiebreak is the case name. This is the ordering
        # that loses documents, and it stays the default until a court can
        # prove better. See #2152
        self.assertEqual(
            list(site.case_names),
            ["Beta v. State", "Alpha v. State", "Gamma v. State"],
        )

    async def test_sort_key_never_reaches_the_output(self):
        """`sort_key` orders the crawl, it is not case data"""
        site = await FakeSite(build_cases()).parse()

        for item in json.loads(site.to_json()):
            self.assertNotIn("sort_key", item)

    async def test_a_partial_sort_key_is_rejected(self):
        """Half a key gives an undefined order, so say so loudly"""
        cases = build_cases()
        del cases[1]["sort_key"]

        with self.assertRaises(InsanityException):
            await FakeSite(cases).parse()


class OrderingContractTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    async def test_recency_ordered_scrapers_supply_a_sort_key(self):
        """A scraper that claims recency ordering must order by a source
        publication time, not by filing date.

        Filing dates repeat, and `_date_sort` breaks those ties by case name,
        which says nothing about when the court published a document. So the
        claim only holds if the scraper hands back a `sort_key`, and only if
        that key is unique enough to give a total order.
        """
        cnt = CaseNameTweaker()
        checked = 0

        for module_string in scraper_modules():
            package, module = module_string.rsplit(".", 1)
            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )
            if not mod.Site.is_recency_ordered:
                continue

            for path in example_paths(module_string):
                with self.subTest(module=module_string, example=path):
                    site = mod.Site(cnt=cnt)
                    site.mock_url = path
                    site.enable_test_mode()
                    await site.parse()
                    if not len(site):
                        continue

                    sort_keys = site._get_sort_keys()
                    self.assertIsNotNone(
                        sort_keys,
                        f"{module_string} sets is_recency_ordered but gives "
                        "no `sort_key`, so it is really ordered by filing "
                        "date. Give each case a `sort_key` taken from a "
                        "source publication time, or drop the claim.",
                    )
                    repeated = [
                        key
                        for key, count in Counter(sort_keys).items()
                        if count > 1
                    ]
                    self.assertFalse(
                        repeated,
                        f"{module_string} repeats these `sort_key` values, so "
                        f"the order within each repeat is arbitrary: "
                        f"{repeated}",
                    )
                    checked += 1

        print(f"\nChecked {checked} recency ordered example file(s).")

    def test_report_scrapers_with_ambiguous_ordering(self):
        """Report which scrapers cannot support the crawl abort.

        Reads the compare files, which hold the output after `_date_sort`, and
        counts the runs of cases that share a date. Inside such a run the order
        comes from the case name tiebreak, so a court that releases a date's
        documents in more than one batch can hide new documents below ones
        already ingested.

        This reports, it does not fail. Most of the fleet is in this state, and
        fixing it needs a publication time that the sources often do not
        expose at all.
        """
        worst = []
        scrapers_with_ties = set()
        total_scrapers = set()
        rows_total = 0
        rows_in_runs = 0

        for path in sorted(
            glob.glob("tests/examples/**/*.compare.json", recursive=True)
        ):
            with open(path) as compare_file:
                data = json.load(compare_file)
            if not isinstance(data, list) or not data:
                continue
            if not isinstance(data[0], dict) or "case_dates" not in data[0]:
                continue

            scraper = os.path.basename(path).split("_example")[0]
            total_scrapers.add(scraper)
            dates = [case.get("case_dates") for case in data]
            rows_total += len(dates)

            longest_run = 1
            run = 1
            for previous, current in zip(dates, dates[1:]):
                run = run + 1 if current == previous else 1
                longest_run = max(longest_run, run)
            rows_in_runs += len(dates) - len(set(dates))

            if longest_run > 1:
                scrapers_with_ties.add(scraper)
                worst.append((longest_run, scraper, len(dates)))

        worst.sort(reverse=True)
        print(
            f"\n{len(scrapers_with_ties)} of {len(total_scrapers)} scrapers "
            f"return cases that share a date; {rows_in_runs} of {rows_total} "
            "rows sit in such a run, where the order is a case name tiebreak "
            "rather than publication order. See #2152.\nLongest runs:"
        )
        for longest_run, scraper, rows in worst[:15]:
            print(
                f"  {scraper:28s} longest same-date run {longest_run:3d} "
                f"of {rows:4d} rows"
            )


if __name__ == "__main__":
    unittest.main()
