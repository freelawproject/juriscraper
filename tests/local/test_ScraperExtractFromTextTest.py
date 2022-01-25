import unittest

from juriscraper.lib.importer import build_module_list
from juriscraper.OpinionSite import OpinionSite


class ScraperExtractFromText(unittest.TestCase):
    """Adds specific tests to specific courts that are more-easily tested
    without a full integration test.
    """

    test_data = {
        "juriscraper.opinions.united_states.administrative_agency.bia": [
            (
                """Matter of Emmanuel LAGUERRE, Respondent \nDecided January 20, 2022 and more """,
                {
                    "OpinionCluster": {
                        "date_filed": "2022-01-20",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
            (
                "Matter of Enrique ALDAY-DOMINGUEZ, Respondent\nDecided June 1, 2017",
                {
                    "OpinionCluster": {
                        "date_filed": "2017-06-01",
                        "date_filed_is_approximate": False,
                    }
                },
            ),
        ],
    }

    def test_extract_from_text(self):
        """Test that extract_from_text returns the expected data."""
        for module_string, test_cases in self.test_data.items():
            package, module = module_string.rsplit(".", 1)
            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )
            site = mod.Site()
            for test_case in test_cases:
                self.assertEqual(
                    site.extract_from_text(test_case[0]), test_case[1]
                )

    def test_extract_from_text_properly_implemented(self):
        """Ensure that extract_from_text is properly implemented."""

        module_strings = build_module_list(
            "juriscraper.opinions.united_states"
        )
        for module_string in module_strings:
            package, module = module_string.rsplit(".", 1)
            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )
            site = mod.Site()
            if mod.Site.extract_from_text == OpinionSite.extract_from_text:
                # Method is not overridden, so skip it.
                continue
            self.assertIn(
                module_string,
                self.test_data.keys(),
                msg=f"{module_string} not yet added to extract_from_text test data.",
            )
