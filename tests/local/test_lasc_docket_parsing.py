# coding=utf-8
import glob
import os
import sys
import time
import unittest

import jsondate3 as json

from juriscraper.lib.test_utils import warn_or_crash_slow_parser

from juriscraper.lasc.fetch import LASCSearch
from tests import TESTS_ROOT_EXAMPLES_LASC


class LASCParseTest(unittest.TestCase):
    """Can we parse LASC dockets?"""

    def setUp(self):
        self.maxDiff = 200000

    def run_parsers_on_path(self, path):
        """Test all the parsers on a given local path

        :param path: The path where you can find the files
        """
        file_paths = glob.glob(path)
        file_paths.sort()
        path_max_len = max(len(path) for path in file_paths) + 2
        for i, path in enumerate(file_paths):
            sys.stdout.write("%s. Doing %s" % (i, path.ljust(path_max_len)))
            t1 = time.time()
            dirname, filename = os.path.split(path)
            filename_sans_ext = filename.split(".")[0]
            json_path = os.path.join(
                dirname, "%s_result.json" % filename_sans_ext
            )

            lasc = LASCSearch(session=None)
            with open(path, "rb") as f:
                data = json.load(f)
                clean_data = lasc._parse_case_data(data)

            if not os.path.isfile(json_path):
                # First time testing this docket
                bar = "*" * 50
                print(
                    "\n\n%s\nJSON FILE DID NOT EXIST. CREATING IT AT:"
                    "\n\n  %s\n\n"
                    "Please test the data in this file before assuming "
                    "everything worked.\n%s\n" % (bar, json_path, bar)
                )
                with open(json_path, "w") as f:
                    json.dump(clean_data, f, indent=2, sort_keys=True)
                    continue

            with open(json_path) as f:
                j = json.load(f)
                self.assertEqual(j, clean_data)

            t2 = time.time()
            duration = t2 - t1
            warn_or_crash_slow_parser(duration, max_duration=1)
            sys.stdout.write("✓ - %0.1fs\n" % (t2 - t1))

    def test_dockets(self):
        path = os.path.join(TESTS_ROOT_EXAMPLES_LASC, "dockets", "*CV.json")
        self.run_parsers_on_path(path)
