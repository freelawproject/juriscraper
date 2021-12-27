#!/usr/bin/env python


import fnmatch
import json
import os
import sys
import time
import unittest

from juriscraper.lib.test_utils import warn_or_crash_slow_parser
from juriscraper.pacer.http import check_if_logged_in_page
from tests import TESTS_ROOT_EXAMPLES_PACER


class PacerNeedLoginTest(unittest.TestCase):
    """Test if different pages require a log in."""

    def parse_files(self, path_root, file_ext):
        paths = []
        for root, dirnames, filenames in os.walk(path_root):
            for filename in fnmatch.filter(filenames, file_ext):
                paths.append(os.path.join(root, filename))
        paths.sort()
        path_max_len = max(len(path) for path in paths) + 2
        for i, path in enumerate(paths):
            t1 = time.time()
            sys.stdout.write(f"{i}. Doing {path.ljust(path_max_len)}")
            dirname, filename = os.path.split(path)
            filename_sans_ext = filename.split(".")[0]
            json_path = os.path.join(dirname, f"{filename_sans_ext}.json")

            with open(path, "rb") as f:
                text = f.read()

            result = check_if_logged_in_page(text)

            if not os.path.exists(json_path):
                with open(json_path, "w") as f:
                    print(f"Creating new file at {json_path}")
                    json.dump(result, f, indent=2, sort_keys=True)
                continue
            with open(json_path) as f:
                j = json.load(f)
                self.assertEqual(j, result)
            t2 = time.time()
            duration = t2 - t1
            warn_or_crash_slow_parser(duration, max_duration=0.5)

            sys.stdout.write("✓\n")

    def test_parsing_auth_samples(self):
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "authentication_samples"
        )
        self.parse_files(path_root, "*.html")
