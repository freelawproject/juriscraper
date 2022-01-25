import json
import os
import unittest
from glob import glob
from typing import List

from juriscraper.lib.importer import build_module_list


class ScraperExtractFromText(unittest.TestCase):
    """Adds specific tests to specific courts that are more-easily tested
    without a full integration test.
    """

    def run_tests_on_module_str(self, module_str: str) -> List[str]:
        """Finds all the $module_example* files and tests them with the sample
        scraper.
        """
        return build_module_list(module_str)

    def test_extract_from_text_properly_implemented(self):
        """Ensure that extract_from_text is properly implemented."""

        module_strings = self.run_tests_on_module_str("juriscraper.opinions")
        for module_string in module_strings:
            if "backscraper" in module_string:
                continue
            package, module = module_string.rsplit(".", 1)
            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )
            site = mod.Site()
            try:
                if site.extract_from_text("This is a test.") == {}:
                    continue
            except:
                # Fail if the extract_from_text method is implemented and test it.
                pass

            module_parts = module_string.split(".")
            example_path = Path("tests") / "examples" / module_parts[1] / "united_states" / module_parts[-1]
            # Run the compare file for any module (non-backscraper) that has extract_from_text implemented.
            with open(f"{example_path}_extract_from_text.compare.json") as f:
                answers = json.load(f)

            sorted_paths = sorted(
                glob(f"{example_path}_extract_from_text*.txt")
            )

            self.assertEqual(
                len(sorted_paths),
                len(answers),
                msg=f"Missing test files for extract_from_text in {module_parts[-1]}",
            )

            for file in sorted(glob(f"{example_path}_extract_from_text*.txt")):
                s = site.extract_from_text(open(file).read())
                self.assertEqual(
                    s,
                    answers.pop(0),
                    msg=f"Extract from text failed with {file}",
                )
