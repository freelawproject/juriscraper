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
                sys.stdout.write(f"{i}. Doing {path.ljust(path_max_len)}")
                t1 = time.time()
                dirname, filename = os.path.split(path)
                filename_sans_ext = filename.split(".")[0]
                json_path = os.path.join(dirname, f"{filename_sans_ext}.json")
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
                sys.stdout.write(f"✓ - {t2 - t1:0.1f}s\n")

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


class DocketAnonymizeTest(unittest.TestCase):
    """Does our docket anonymizer work?"""

    def assert_anonymized(
        self, path: str, skip_pre_test: bool = False
    ) -> None:
        report = DocketReport("akd")
        with open(path, "rb") as f:
            text = f.read().decode("utf-8")

        if not skip_pre_test:
            self.assertIn("LOGIN REMOVED", text)
        report._parse_text(text)
        anon_text = report.get_anonymized_text()
        self.assertNotIn("LOGIN REMOVED", anon_text)

    def test_anonymize_district(self) -> None:
        path = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER_DOCKET,
            "district",
            "akd.html",
        )
        self.assert_anonymized(path)

    def test_anonymize_bankruptcy(self) -> None:
        path = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER_DOCKET,
            "bankruptcy",
            "akb.html",
        )
        self.assert_anonymized(path)

    def test_anonymize_specialty(self) -> None:
        path = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER_DOCKET,
            "special",
            "cit.html",
        )
        self.assert_anonymized(path)

    def test_not_docket_dockets(self) -> None:
        path = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER_DOCKET,
            "not_dockets",
            "cacd_628915.html",
        )
        # Some things we get back from RECAP are not actually dockets. Normally
        # the assert_anonymized method checks that the username is there before
        # and then gone after running the anonymize function. But since these
        # aren't actually dockets, it isn't there ahead of time. In that case,
        # skip the before test.
        self.assert_anonymized(path, skip_pre_test=True)


class DocketNumberParseTest(unittest.TestCase):
    """Assert docket number components parsing."""

    def test_district_docket_number_components_parsing(self) -> None:
        report = DocketReport("akd")

        test_cases = [
            (
                "1:01-cv-00570-PCH",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cv",
                    "federal_dn_judge_initials_assigned": "PCH",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "2:20-mc-00021-JES-M_M",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "mc",
                    "federal_dn_judge_initials_assigned": "JES",
                    "federal_dn_judge_initials_referred": "M_M",
                    "federal_dn_office_code": "2",
                },
            ),
            (
                "2:20-mc-00021-JES-g_g",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "mc",
                    "federal_dn_judge_initials_assigned": "JES",
                    "federal_dn_judge_initials_referred": "g_g",
                    "federal_dn_office_code": "2",
                },
            ),
            (
                "1:20-cv-00021-GBD-SLC",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cv",
                    "federal_dn_judge_initials_assigned": "GBD",
                    "federal_dn_judge_initials_referred": "SLC",
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "1:20-cr-00033-CJW-MAR",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cr",
                    "federal_dn_judge_initials_assigned": "CJW",
                    "federal_dn_judge_initials_referred": "MAR",
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "2:20-sw-00156-tmp",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "sw",
                    "federal_dn_judge_initials_assigned": "tmp",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "2",
                },
            ),
            (
                "3:20-cr-00061-TMB-MMS",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cr",
                    "federal_dn_judge_initials_assigned": "TMB",
                    "federal_dn_judge_initials_referred": "MMS",
                    "federal_dn_office_code": "3",
                },
            ),
            (
                "1:20-mj-00061-N",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "mj",
                    "federal_dn_judge_initials_assigned": "N",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "1:20-mj-00061-N-1",
                {
                    "federal_defendant_number": "1",
                    "federal_dn_case_type": "mj",
                    "federal_dn_judge_initials_assigned": "N",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "1:20-mj-00061-N-2",
                {
                    "federal_defendant_number": "2",
                    "federal_dn_case_type": "mj",
                    "federal_dn_judge_initials_assigned": "N",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "1:20-cr-00061-KD",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cr",
                    "federal_dn_judge_initials_assigned": "KD",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "1:20-cr-00060-CG-N",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cr",
                    "federal_dn_judge_initials_assigned": "CG",
                    "federal_dn_judge_initials_referred": "N",
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "4:20-cv-00059-AW-MJF",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cv",
                    "federal_dn_judge_initials_assigned": "AW",
                    "federal_dn_judge_initials_referred": "MJF",
                    "federal_dn_office_code": "4",
                },
            ),
            (
                "3:20-cv-00059-MCR-GRJ",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cv",
                    "federal_dn_judge_initials_assigned": "MCR",
                    "federal_dn_judge_initials_referred": "GRJ",
                    "federal_dn_office_code": "3",
                },
            ),
            (
                "2:20-mj-00061-MHB",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "mj",
                    "federal_dn_judge_initials_assigned": "MHB",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "2",
                },
            ),
            (
                "1:20-cv-00120-WJM-KMT",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cv",
                    "federal_dn_judge_initials_assigned": "WJM",
                    "federal_dn_judge_initials_referred": "KMT",
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "3:20-cv-00021-GFVT-EBA",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cv",
                    "federal_dn_judge_initials_assigned": "GFVT",
                    "federal_dn_judge_initials_referred": "EBA",
                    "federal_dn_office_code": "3",
                },
            ),
            (
                "8:20-cr-00006-DOC",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cr",
                    "federal_dn_judge_initials_assigned": "DOC",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "8",
                },
            ),
            (
                "2:16-CM-27244-CMR",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "CM",
                    "federal_dn_judge_initials_assigned": "CMR",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "2",
                },
            ),
            (
                "2:16-PV-27244-CMR",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "PV",
                    "federal_dn_judge_initials_assigned": "CMR",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "2",
                },
            ),
            (
                "2:16-AL-27244-CMR",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "AL",
                    "federal_dn_judge_initials_assigned": "CMR",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "2",
                },
            ),
            (
                "2:16-a2-27244-CMR",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "a2",
                    "federal_dn_judge_initials_assigned": "CMR",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "2",
                },
            ),
            (
                "3:21-~gr-00001",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "~gr",
                    "federal_dn_judge_initials_assigned": None,
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "3",
                },
            ),
            (
                "3:21-y-00001",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "y",
                    "federal_dn_judge_initials_assigned": None,
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "3",
                },
            ),
            (
                "1:21-2255-00001",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "2255",
                    "federal_dn_judge_initials_assigned": None,
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "1:21-MDL-00001",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "MDL",
                    "federal_dn_judge_initials_assigned": None,
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "1:21-adc-00001",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "adc",
                    "federal_dn_judge_initials_assigned": None,
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "1:21-crcor-00001",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "crcor",
                    "federal_dn_judge_initials_assigned": None,
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "2:24-gj-00075-JS-1",
                {
                    "federal_defendant_number": "1",
                    "federal_dn_case_type": "gj",
                    "federal_dn_judge_initials_assigned": "JS",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "2",
                },
            ),
            (
                "3:20-cr-00070-TKW-MAL-1",
                {
                    "federal_defendant_number": "1",
                    "federal_dn_case_type": "cr",
                    "federal_dn_judge_initials_assigned": "TKW",
                    "federal_dn_judge_initials_referred": "MAL",
                    "federal_dn_office_code": "3",
                },
            ),
            (
                "3:20-cr-00070-TKW-2",
                {
                    "federal_defendant_number": "2",
                    "federal_dn_case_type": "cr",
                    "federal_dn_judge_initials_assigned": "TKW",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "3",
                },
            ),
            (
                "4:20-mj-00061-N/A",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "mj",
                    "federal_dn_judge_initials_assigned": "N/A",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "4",
                },
            ),
            (
                "4:20-cv-00061-CKJ-PSOT",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cv",
                    "federal_dn_judge_initials_assigned": "CKJ",
                    "federal_dn_judge_initials_referred": "PSOT",
                    "federal_dn_office_code": "4",
                },
            ),
            (
                "1:15-mc-00105-P1",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "mc",
                    "federal_dn_judge_initials_assigned": "P1",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "1:17-cr-00350-KBF-27",
                {
                    "federal_defendant_number": "27",
                    "federal_dn_case_type": "cr",
                    "federal_dn_judge_initials_assigned": "KBF",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "1:08-cv-00398-GWC-TCS-LMG",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "cv",
                    "federal_dn_judge_initials_assigned": "GWC",
                    "federal_dn_judge_initials_referred": "TCS",
                    "federal_dn_office_code": "1",
                },
            ),
        ]

        for test in test_cases:
            with self.subTest("Assert docket_number components", test=test):
                dn_components = report._parse_dn_components(test[0])
                self.assertEqual(
                    dn_components,
                    test[1],
                    msg="The docket number components didn't match.",
                )

    def test_bankruptcy_docket_number_components_parsing(self) -> None:
        report = DocketReport("akb")

        test_cases = [
            (
                "1:24-bk-10757",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": "bk",
                    "federal_dn_judge_initials_assigned": None,
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "02-00017-LMK",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": None,
                    "federal_dn_judge_initials_assigned": "LMK",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": None,
                },
            ),
            (
                "15-32065-bjh11",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": None,
                    "federal_dn_judge_initials_assigned": "bjh",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": None,
                },
            ),
            (
                "09-80591-JAC7",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": None,
                    "federal_dn_judge_initials_assigned": "JAC",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": None,
                },
            ),
            (
                "04-45661-rfn13",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": None,
                    "federal_dn_judge_initials_assigned": "rfn",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": None,
                },
            ),
            (
                "10-01083-8-RDD",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": None,
                    "federal_dn_judge_initials_assigned": "RDD",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "8",
                },
            ),
            (
                "10-12431-1-rel",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": None,
                    "federal_dn_judge_initials_assigned": "rel",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": "1",
                },
            ),
            (
                "13-07422-RLM-7A",
                {
                    "federal_defendant_number": None,
                    "federal_dn_case_type": None,
                    "federal_dn_judge_initials_assigned": "RLM",
                    "federal_dn_judge_initials_referred": None,
                    "federal_dn_office_code": None,
                },
            ),
        ]

        for test in test_cases:
            with self.subTest("Assert docket_number components", test=test):
                dn_components = report._parse_dn_components(test[0])
                self.assertEqual(
                    dn_components,
                    test[1],
                    msg="The docket number components didn't match.",
                )
