#!/usr/bin/env python


import glob
import json
import logging
import os
import sys
import time
import unittest

from juriscraper.lib.importer import build_module_list
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.test_utils import (
    warn_generated_compare_file,
    warn_or_crash_slow_parser,
)


class ScraperExampleTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = 1000
        # Disable logging
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # Re-enable logging
        logging.disable(logging.NOTSET)

    def run_tests_on_module_str(self, module_str: str) -> None:
        """Finds all the $module_example* files and tests them with the sample
        scraper.
        """
        module_strings = build_module_list(module_str)
        num_scrapers = len(
            [s for s in module_strings if "backscraper" not in s]
        )
        max_len_mod_string = (
            max(len(mod) for mod in module_strings if "backscraper" not in mod)
            + 2
        )
        num_example_files = 0
        num_warnings = 0
        cnt = CaseNameTweaker()
        json_compare_extension = ".compare.json"
        json_compare_files_generated = []
        for module_string in module_strings:
            package, module = module_string.rsplit(".", 1)
            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )
            if "backscraper" in module_string:
                continue

            sys.stdout.write(f"  {module_string.ljust(max_len_mod_string)} ")
            sys.stdout.flush()
            # module_parts:
            # [0]  - "juriscraper"
            # [1]  - "opinions" or "oral_args"
            # ...  - rest of the path
            # [-1] - module name
            module_parts = module_string.split(".")
            example_path = os.path.join(
                "tests",
                "examples",
                module_parts[1],
                "united_states",
                module_parts[-1],
            )
            paths = [
                path
                for path in glob.glob(f"{example_path}_example*")
                if not path.endswith(json_compare_extension)
            ]
            self.assertTrue(
                paths,
                "No example file found for: %s! \n\nThe test looked in: "
                "%s"
                % (
                    module_string.rsplit(".", 1)[1],
                    os.path.join(os.getcwd(), example_path),
                ),
            )
            num_example_files += len(paths)
            t1 = time.time()
            num_tests = len(paths)
            for path in paths:
                # This loop allows multiple example files per module
                if path.endswith("~"):
                    # Text editor backup: Not interesting.
                    continue
                site = mod.Site(cnt=cnt)
                site.url = path
                # Forces a local GET
                site.enable_test_mode()
                site.parse()
                # Now validate that the parsed result is as we expect
                json_path = f"{path.rsplit('.', 1)[0]}{json_compare_extension}"
                json_data = json.loads(site.to_json())
                if os.path.isfile(json_path):
                    # Compare result with corresponding json file
                    example_file = path.rsplit("/", 1)[1]
                    compare_file = json_path.rsplit("/", 1)[1]
                    with (
                        open(json_path) as input_file,
                        self.subTest(
                            "Testing example files",
                            json_path=json_path,
                            module_string=module_string,
                        ),
                    ):
                        fixture_json = json.load(input_file)
                        self.assertEqual(
                            len(fixture_json),
                            len(json_data),
                            msg="Fixture and scraped data have different "
                            "lengths: expected %s and scraped %s (%s)"
                            % (
                                len(fixture_json),
                                len(json_data),
                                module_string,
                            ),
                        )
                        for i, item in enumerate(fixture_json):
                            self.assertEqual(
                                fixture_json[i],
                                json_data[i],
                            )

                else:
                    # Generate corresponding json file if it doesn't
                    # already exist. This should only happen once
                    # when adding a new example html file.
                    warn_generated_compare_file(json_path)
                    json_compare_files_generated.append(json_path)
                    with open(json_path, "w") as json_example:
                        json.dump(json_data, json_example, indent=2)
            t2 = time.time()
            duration = t2 - t1
            warning_msg = warn_or_crash_slow_parser(t2 - t1)
            if warning_msg:
                num_warnings += 1

            print(f"({num_tests} test(s) in {duration:0.1f} seconds)")

        print(
            "\n{num_scrapers} scrapers tested successfully against "
            "{num_example_files} example files, with {num_warnings} "
            "speed warnings.".format(
                num_scrapers=num_scrapers,
                num_example_files=num_example_files,
                num_warnings=num_warnings,
            )
        )
        if json_compare_files_generated:
            msg = (
                "Generated compare file(s) during test, please review before proceeding. "
                "If the data looks good, run tests again, then be sure to include "
                "the new compare file(s) in your commit: %s"
            )
            self.fail(msg % ", ".join(json_compare_files_generated))
        if num_warnings:
            print(
                "\nAt least one speed warning was triggered during the "
                "tests. If this is due to a slow scraper you wrote, we "
                "suggest attempting to speed it up, as it will be slow "
                "both in production and while running tests. This is "
                "currently a warning, but may raise a failure in the "
                "future as performance requirements are tightened."
            )
        else:
            # Someday, this line of code will be run. That day is not today.
            print(
                "\nNo speed warnings detected. That's great, keep up the "
                "good work!"
            )

    def test_scrape_opinion_admin_example_files(self):
        self.run_tests_on_module_str(
            "juriscraper.opinions.united_states.administrative_agency"
        )

    def test_scrape_opinion_fed_app_example_files(self):
        self.run_tests_on_module_str(
            "juriscraper.opinions.united_states.federal_appellate"
        )

    def test_scrape_opinion_fed_bankr_example_files(self):
        self.run_tests_on_module_str(
            "juriscraper.opinions.united_states.federal_bankruptcy"
        )

    def test_scrape_opinion_fed_dist_example_files(self):
        self.run_tests_on_module_str(
            "juriscraper.opinions.united_states.federal_district"
        )

    def test_scrape_opinion_fed_special_example_files(self):
        self.run_tests_on_module_str(
            "juriscraper.opinions.united_states.federal_special"
        )

    def test_scrape_opinion_state_example_files(self):
        self.run_tests_on_module_str(
            "juriscraper.opinions.united_states.state"
        )

    def test_scrape_oral_arg_example_files(self):
        self.run_tests_on_module_str("juriscraper.oral_args")

    def test_scrape_opinion_territories_example_files(self):
        self.run_tests_on_module_str(
            "juriscraper.opinions.united_states.territories"
        )
