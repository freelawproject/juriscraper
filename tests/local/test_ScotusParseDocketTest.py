import os
import unittest

from juriscraper.scotus import SCOTUSDocketReport
from tests import TESTS_ROOT_EXAMPLES_SCOTUS
from tests.local.PacerParseTestCase import PacerParseTestCase


class ScotusParseDocketTest(PacerParseTestCase):
    """Can we parse the scotus dockets effectively?"""

    def setUp(self):
        self.maxDiff = 200000

    def test_parsing_scotus_json_dockets(self):
        path_root = os.path.join(TESTS_ROOT_EXAMPLES_SCOTUS, "dockets", "json")
        self.parse_files(path_root, "*.compare.json", SCOTUSDocketReport)


class LowerCourtCasesCleaningTest(unittest.TestCase):
    """Test the SCOTUSDocketReport clean_lower_court_cases method"""

    def setUp(self):
        self.parser = SCOTUSDocketReport()

    def test_clean_lower_court_cases(self):
        cases = {
            # Case 1: Slash-separated numbers with same prefix
            "98-35309/35509": ["98-35309", "98-35509"],
            "96-C-235/239/240/241": [
                "96-C-235",
                "96-C-239",
                "96-C-240",
                "96-C-241",
            ],
            # Case 2: Negative prefix-separated (commas/semicolons/trailing dash)
            "99-1845,-1846,-1847,-197": [
                "99-1845",
                "99-1846",
                "99-1847",
                "99-197",
            ],
            "98-4033;-4214;-4246": ["98-4033", "98-4214", "98-4246"],
            "98-60240,-60454,-60467,-": ["98-60240", "98-60454", "98-60467"],
            # Case 3: Comma-separated with correct prefixes
            "33094-CW,33095-CW": ["33094-CW", "33095-CW"],
            # Case 6: Ampersand / See also
            "95-56639 & 96-55194": ["95-56639", "96-55194"],
            "95-56639 See also 96-55194": ["95-56639", "96-55194"],
            # Case 7: Special formats
            "CR-99-1140": ["CR-99-1140"],
            "1998-CA-0022039-MR": ["1998-CA-0022039-MR"],
            # Case 8: Range expansion
            "97-1715/98-1111 to 1115": [
                "97-1715",
                "98-1111",
                "98-1112",
                "98-1113",
                "98-1114",
                "98-1115",
            ],
            "97-1715/1111 to 1115": [
                "97-1715",
                "97-1111",
                "97-1112",
                "97-1113",
                "97-1114",
                "97-1115",
            ],
            # Default cleanup path (mixed separators & newlines)
            "98-123; 98-124\n98-125 & 98-126": [
                "98-123",
                "98-124",
                "98-125",
                "98-126",
            ],
            # Parentheses removal
            "(98-4033;-4214)": ["98-4033", "98-4214"],
        }

        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(
                    expected, self.parser.clean_lower_court_cases(raw)
                )
