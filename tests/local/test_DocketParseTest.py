# coding=utf-8


import fnmatch
import os
import sys
import time
import unittest

import jsondate3 as json

from juriscraper.lib.test_utils import warn_or_crash_slow_parser
from juriscraper.pacer import DocketReport
from tests import TESTS_ROOT_EXAMPLES_PACER

TESTS_ROOT_EXAMPLES_PACER_DOCKET = os.path.join(
    TESTS_ROOT_EXAMPLES_PACER, "dockets"
)


class DocketParseTest(unittest.TestCase):
    """Lots of docket parsing tests."""

    def setUp(self):
        self.maxDiff = 200000

    def run_parsers_on_path(
        self,
        path_root,
        required_fields=["date_filed", "case_name", "docket_number"],
    ):
        """Test all the parsers, faking the network query."""
        paths = []
        for root, dirnames, filenames in os.walk(path_root):
            for filename in fnmatch.filter(filenames, "*.html"):
                paths.append(os.path.join(root, filename))
        paths.sort()
        path_max_len = max(len(path) for path in paths) + 2
        for i, path in enumerate(paths):
            with self.subTest("Checking parsers", path=path):
                sys.stdout.write(
                    "%s. Doing %s" % (i, path.ljust(path_max_len))
                )
                t1 = time.time()
                dirname, filename = os.path.split(path)
                filename_sans_ext = filename.split(".")[0]
                json_path = os.path.join(
                    dirname, "%s.json" % filename_sans_ext
                )
                court = filename_sans_ext.split("_")[0]

                report = DocketReport(court)
                with open(path, "rb") as f:
                    report._parse_text(f.read().decode("utf-8"))
                data = report.data

                if data != {}:
                    # If the docket is a valid docket, make sure some required
                    # fields are populated.
                    for field in required_fields:
                        self.assertTrue(
                            data[field],
                            msg="Unable to find truthy value for field %s"
                            % field,
                        )

                    self.assertEqual(data["court_id"], court)

                    # Party-specific tests...
                    for party in data["parties"]:
                        self.assertTrue(
                            party.get("name", False),
                            msg="Every party must have a name attribute. Did not "
                            "get a value for:\n\n%s" % party,
                        )
                        # Protect against effed up adversary proceedings cases that
                        # don't parse properly. See: cacb, 2:08-ap-01570-BB
                        self.assertNotIn("----", party["name"])

                if not os.path.isfile(json_path):
                    bar = "*" * 50
                    print(
                        "\n\n%s\nJSON FILE DID NOT EXIST. CREATING IT AT:"
                        "\n\n  %s\n\n"
                        "Please test the data in this file before assuming "
                        "everything worked.\n%s\n" % (bar, json_path, bar)
                    )
                    with open(json_path, "w") as f:
                        json.dump(data, f, indent=2, sort_keys=True)
                        # self.assertFalse(True)
                        continue

                with open(json_path) as f:
                    j = json.load(f)
                    if j != {}:
                        # Compare docket entries and parties first, for easier
                        # debugging, then compare whole objects to be sure.
                        self.assertEqual(
                            j["docket_entries"], data["docket_entries"]
                        )
                        self.assertEqual(j["parties"], data["parties"])
                    self.assertEqual(j, data)
                t2 = time.time()

                duration = t2 - t1
                warn_or_crash_slow_parser(duration, max_duration=1)
                sys.stdout.write("✓ - %0.1fs\n" % (t2 - t1))

    def test_bankruptcy_court_dockets(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER_DOCKET, "bankruptcy"
        )
        self.run_parsers_on_path(path_root)

    def test_district_court_dockets(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER_DOCKET, "district")
        self.run_parsers_on_path(path_root)

    def test_fakerss_court_dockets(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER_DOCKET, "fake-rss")
        self.run_parsers_on_path(
            path_root,
            required_fields=[
                "case_name",
                "docket_number",
            ],
        )

    def test_specialty_court_dockets(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_PACER_DOCKET, "special")
        self.run_parsers_on_path(path_root)

    def test_not_docket_dockets(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER_DOCKET, "not_dockets"
        )
        self.run_parsers_on_path(path_root)
