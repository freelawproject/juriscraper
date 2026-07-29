#!/usr/bin/env python

import glob
import os
import unittest

from juriscraper.lib.importer import build_module_list
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.test_utils import warn_generated_compare_file

FIXTURE_DIR = os.path.join("tests", "examples", "opinions", "cleanup_content")
COMPARE_EXTENSION = ".compare.html"


class ScraperCleanupContentTest(unittest.TestCase):
    """Test Site.cleanup_content against real downloaded documents

    Fixtures live in tests/examples/opinions/cleanup_content/ and are named
    `<module_name>_<label>.html`, holding a document exactly as downloaded
    from the source. Each is run through the matching scraper's
    `cleanup_content` and compared against `<module_name>_<label>.compare.html`.

    Like ScraperExampleTest's compare.json files, a missing compare file is
    generated from the actual output and the test run fails; review it and
    run again.
    """

    def test_cleanup_content_fixtures(self):
        module_strings = build_module_list("juriscraper.opinions")
        modules_by_name = {
            module_string.rsplit(".", 1)[1]: module_string
            for module_string in module_strings
            if "backscraper" not in module_string
        }
        paths = sorted(
            path
            for path in glob.glob(os.path.join(FIXTURE_DIR, "*.html"))
            if not path.endswith(COMPARE_EXTENSION)
        )
        self.assertTrue(paths, f"No fixture files found in {FIXTURE_DIR}")

        compare_files_generated = []
        for path in paths:
            fixture_name = os.path.basename(path).rsplit(".", 1)[0]
            # A module name may itself contain underscores (nyappdiv_1st),
            # so match the longest module name prefixing the fixture name
            matches = [
                name
                for name in modules_by_name
                if fixture_name.startswith(f"{name}_")
            ]
            self.assertTrue(
                matches, f"No scraper module matches fixture '{path}'"
            )
            module_string = modules_by_name[max(matches, key=len)]
            package, module = module_string.rsplit(".", 1)
            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )
            site = mod.Site(cnt=CaseNameTweaker())

            with open(path, "rb") as fixture_file:
                content = fixture_file.read()
            cleaned = site.cleanup_content(content)
            if isinstance(cleaned, str):
                cleaned = cleaned.encode()

            compare_path = f"{path.rsplit('.', 1)[0]}{COMPARE_EXTENSION}"
            if os.path.isfile(compare_path):
                with (
                    open(compare_path, "rb") as compare_file,
                    self.subTest(
                        "Testing cleanup_content fixtures",
                        fixture=path,
                        module_string=module_string,
                    ),
                ):
                    self.assertEqual(compare_file.read(), cleaned)
            else:
                warn_generated_compare_file(compare_path)
                compare_files_generated.append(compare_path)
                with open(compare_path, "wb") as compare_file:
                    compare_file.write(cleaned)

        if compare_files_generated:
            self.fail(
                "Generated compare file(s) during test, please review before "
                "proceeding. If the data looks good, run tests again, then be "
                "sure to include the new compare file(s) in your commit: "
                f"{', '.join(compare_files_generated)}"
            )
