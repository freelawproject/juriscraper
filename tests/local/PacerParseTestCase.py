# coding=utf-8


import fnmatch
import os
import sys
import time
import unittest

import jsondate3 as json

from juriscraper.lib.test_utils import warn_or_crash_slow_parser


class PacerParseTestCase(unittest.TestCase):
    """A mixin to add a parsing test."""

    def parse_files(self, path_root, file_ext, test_class):
        """Can we do a simple query and parse?"""
        paths = []
        for root, dirnames, filenames in os.walk(path_root):
            for filename in fnmatch.filter(filenames, file_ext):
                paths.append(os.path.join(root, filename))
        paths.sort()
        path_max_len = max(len(path) for path in paths) + 2
        for i, path in enumerate(paths):
            t1 = time.time()
            sys.stdout.write("%s. Doing %s" % (i, path.ljust(path_max_len)))
            dirname, filename = os.path.split(path)
            filename_sans_ext = filename.split(".")[0]
            json_path = os.path.join(dirname, "%s.json" % filename_sans_ext)

            court = filename_sans_ext.split("_")[0]
            report = test_class(court)
            with open(path, "r") as f:
                report._parse_text(f.read())

            # Does the metadata function work too? It usually, but not always,
            # gets called by report.data
            try:
                _ = report.metadata
            except AttributeError:
                # Some reports don't have this method.
                pass
            data = report.data
            if not os.path.exists(json_path):
                with open(json_path, "w") as f:
                    print("Creating new file at %s" % json_path)
                    json.dump(data, f, indent=2, sort_keys=True)
                continue
            data = json.loads(json.dumps(data, sort_keys=True))
            with open(json_path) as f:
                j = json.load(f)
                with self.subTest(
                    "Parsing PACER", file=filename, klass=test_class
                ):
                    self.assertEqual(j, data)
            t2 = time.time()
            duration = t2 - t1
            warn_or_crash_slow_parser(duration, max_duration=2)

            sys.stdout.write("✓\n")
