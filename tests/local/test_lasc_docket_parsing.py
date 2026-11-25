import pathlib
import sys
import time
import unittest

import jsondate3 as json

from juriscraper.lasc.fetch import LASCSearch
from juriscraper.lib.test_utils import warn_or_crash_slow_parser
from tests import TESTS_ROOT_EXAMPLES_LASC


class LASCParseTest(unittest.TestCase):
    """Can we parse LASC dockets?"""

    def setUp(self):
        self.maxDiff = 200000

    def run_parsers_on_path(self, directory, pattern):
        """Test all the parsers on a given local path

        :param directory: The directory where you can find the files
        :param pattern: Glob pattern matching the files to parse
        """
        file_paths = sorted(pathlib.Path(directory).glob(pattern))
        path_max_len = max(len(str(path)) for path in file_paths) + 2
        for i, path in enumerate(file_paths):
            sys.stdout.write(f"{i}. Doing {str(path).ljust(path_max_len)}")
            t1 = time.time()
            filename_sans_ext = path.name.split(".")[0]
            json_path = path.parent / f"{filename_sans_ext}_result.json"

            lasc = LASCSearch(session=None)
            with path.open("rb") as f:
                data = json.load(f)
                clean_data = lasc._parse_case_data(data)

            if not json_path.is_file():
                # First time testing this docket
                bar = "*" * 50
                print(
                    "\n\n%s\nJSON FILE DID NOT EXIST. CREATING IT AT:"
                    "\n\n  %s\n\n"
                    "Please test the data in this file before assuming "
                    "everything worked.\n%s\n" % (bar, json_path, bar)
                )
                with json_path.open("w") as f:
                    json.dump(clean_data, f, indent=2, sort_keys=True)
                    continue

            with json_path.open() as f:
                j = json.load(f)
                self.assertEqual(j, clean_data)

            t2 = time.time()
            duration = t2 - t1
            warn_or_crash_slow_parser(duration, max_duration=1)
            sys.stdout.write(f"✓ - {t2 - t1:0.1f}s\n")

    def test_dockets(self):
        self.run_parsers_on_path(
            TESTS_ROOT_EXAMPLES_LASC / "dockets", "*CV.json"
        )
