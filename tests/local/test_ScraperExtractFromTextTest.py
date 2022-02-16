import unittest

from juriscraper.lib.importer import build_module_list
from juriscraper.OpinionSite import OpinionSite


class ScraperExtractFromText(unittest.TestCase):
    """Adds specific tests to specific courts that are more-easily tested
    without a full integration test.
    """

    # To avoid AssertionError when comparing example results for Colorado Appellate
    maxDiff = None
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
        "juriscraper.opinions.united_states.state.nm": [
            (
                """Opinion Number: _______________ Filing Date: January 10, 2022\nNO. S-1-SC-38247\nCITIZENS FOR FAIR RATES""",
                {"OpinionCluster": {"docket_number": "S-1-SC-38247"}},
            )
        ],
        "juriscraper.opinions.united_states.state.nmctapp": [
            (
                """Opinion Number: _______________ Filing Date: January 10, 2022\nNo. A-1-CA-39059\nCITIZENS FOR FAIR RATES""",
                {"OpinionCluster": {"docket_number": "A-1-CA-39059"}},
            )
        ],
        "juriscraper.opinions.united_states.state.ark": [
            (
                """HONORABLE JODI RAINES DENNIS,\nCite as 2022 Ark. 19\nSUPREME COURT OF ARKANSAS No. CV-21-173\n  ARKANSAS DEPARTMENT OF CORRECTION""",
                {"OpinionCluster": {"docket_number": "CV-21-173"}},
            ),
            # Some opinions don't have dockets because Arkansas publishes important announcements.
            (
                """Cite as 2022 Ark. 14\nSUPREME COURT OF ARKANSAS Opinion Delivered: January 27, 2022""",
                {"OpinionCluster": {"docket_number": ""}},
            ),
        ],
        "juriscraper.opinions.united_states.state.arkctapp": [
            (
                """Cite as 2022 Ark. App. 51\nARKANSAS COURT OF APPEALS\nDIVISION II No. CV-20-579\n  ADDAM MAXWELL V.\nLORI MAXWELL""",
                {"OpinionCluster": {"docket_number": "CV-20-579"}},
            ),
            (
                """Cite as 2022 Ark. App. 43\nARKANSAS COURT OF APPEALS\nDIVISION IV No. E-21-215\n  FRED JACKSON""",
                {"OpinionCluster": {"docket_number": "E-21-215"}},
            ),
        ],
        "juriscraper.opinions.united_states.state.colo": [
            (
                """                 The Supreme Court of the State of Colorado\n                 2 East 14th Avenue • Denver, Colorado 80203\n\n                                   2020 CO 6\n\n                      Supreme Court Case No. 20SC758\n                    Certiorari to the Colorado Court of Appeals\n                      Court of Appeals Case No. 18CA38\n""",
                {
                    "OpinionCluster": {"docket_number": "20SC758"},
                    "Citation": {
                        "volume": "2020",
                        "reporter": "CO",
                        "page": "6",
                        "type": 2,
                    },
                },
            ),
        ],
        "juriscraper.opinions.united_states.state.coloctapp": [
            (
                """     The summaries of the Colorado Court of Appeals published opinions\n  constitute no part of the opinion of the division but have been prepared by\n  the division for the convenience of the reader. The summaries may not be\n    cited or relied upon as they are not the official language of the division.\n  Any discrepancy between the language in the summary and in the opinion\n           should be resolved in favor of the language in the opinion.\n\n\n                                                                 SUMMARY\n                                                          September 9, 2021\n\n                               2021COA122\n\nNo. 20CA0621, Cummings v. Arapahoe Cnty. Sheriff’s Office —\nGovernment — County Officers — Sheriff — Deputies\n\n     A division of the court of appeals applies the holding from\n\nCummings v. Arapahoe County Sheriff’s Department, 2018 COA 136,\n\nto a sheriff’s personnel policy granting notice of an investigation and\n\nprovides guidance as to the scope of Cummings and section 30-10-\n\n506, C.R.S. 2020. Because the subject policy did not effectuate the\n\nspecific right section 30-10-506 grants a deputy — the right to\n\nnotice “of the reason for the proposed revocation” of his employment\n\n— the division concludes the policy was not contractually binding.\n\nAccordingly, the district court erred by instructing the jury to\n\nconsider the sheriff’s compliance with the policy in determining\n\nwhether he breached an implied employment contract.\nCOLORADO COURT OF APPEALS                                        2021COA122\n\n\nCourt of Appeals No. 20CA0621\nArapahoe County District Court No. 16CV32444\nHonorable Kenneth M. Plotz, Judge\n""",
                {
                    "OpinionCluster": {
                        "docket_number": "20CA0621",
                        "headnotes": "Cummings v. Arapahoe Cnty. Sheriff's Office — Government — County Officers — Sheriff — Deputies",
                        "summary": """A division of the court of appeals applies the holding from Cummings v. Arapahoe County Sheriff's Department, 2018 COA 136, to a sheriff's personnel policy granting notice of an investigation and provides guidance as to the scope of Cummings and section 30-10- 506, C.R.S. 2020. Because the subject policy did not effectuate the specific right section 30-10-506 grants a deputy — the right to notice "of the reason for the proposed revocation" of his employment — the division concludes the policy was not contractually binding. Accordingly, the district court erred by instructing the jury to consider the sheriff's compliance with the policy in determining whether he breached an implied employment contract.""",
                    },
                    "Citation": {
                        "volume": "2021",
                        "reporter": "COA",
                        "page": "122",
                        "type": 2,
                    },
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
