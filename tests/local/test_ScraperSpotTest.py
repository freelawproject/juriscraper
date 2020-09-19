#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest

from juriscraper.opinions.united_states.state import colo, mass, massappct, nh
from juriscraper.oral_args.united_states.federal_appellate import ca6


class ScraperSpotTest(unittest.TestCase):
    """Adds specific tests to specific courts that are more-easily tested
    without a full integration test.
    """

    def test_mass(self):
        strings = {
            "Massachusetts State Automobile Dealers Association, Inc. v. Tesla Motors MA, Inc. (SJC 11545) (September 15, 2014)": [
                "Massachusetts State Automobile Dealers Association, Inc. v. Tesla Motors MA, Inc.",
                "SJC 11545",
            ],
            "Bower v. Bournay-Bower (SJC 11478) (September 15, 2014)": [
                "Bower v. Bournay-Bower",
                "SJC 11478",
            ],
            "Commonwealth v. Holmes (SJC 11557) (September 12, 2014)": [
                "Commonwealth v. Holmes",
                "SJC 11557",
            ],
            "Superintendent-Director of Assabet Valley Regional School District v. Speicher (SJC 11563) (September 11, 2014)": [
                "Superintendent-Director of Assabet Valley Regional School District v. Speicher",
                "SJC 11563",
            ],
            "Commonwealth v. Quinn (SJC 11554) (September 11, 2014)": [
                "Commonwealth v. Quinn",
                "SJC 11554",
            ],
            "Commonwealth v. Wall (SJC 09850) (September 11, 2014)": [
                "Commonwealth v. Wall",
                "SJC 09850",
            ],
            "Commonwealth v. Letkowski (SJC 11556) (September 9, 2014)": [
                "Commonwealth v. Letkowski",
                "SJC 11556",
            ],
            "Commonwealth v. Sullivan (SJC 11568) (September 9, 2014)": [
                "Commonwealth v. Sullivan",
                "SJC 11568",
            ],
            "Plumb v. Casey (SJC 11519) (September 8, 2014)": [
                "Plumb v. Casey",
                "SJC 11519",
            ],
            "A.J. Properties, LLC v. Stanley Black and Decker, Inc. (SJC 11424) (September 5, 2014)": [
                "A.J. Properties, LLC v. Stanley Black and Decker, Inc.",
                "SJC 11424",
            ],
            "Massachusetts Electric Co. v. Department of Public Utilities (SJC 11526, 11527, 11528) (September 4, 2014)": [
                "Massachusetts Electric Co. v. Department of Public Utilities",
                "SJC 11526, 11527, 11528",
            ],
            "Commonwealth v. Doe (SJC-11861) (October 22, 2015)": [
                "Commonwealth v. Doe",
                "SJC-11861",
            ],
            "Commonwealth v. Teixeira; Commonwealth v. Meade (SJC 11929; SJC 11944) (September 16, 2016)": [
                "Commonwealth v. Teixeira; Commonwealth v. Meade",
                "SJC 11929; SJC 11944",
            ],
        }
        self.validate_mass_string_parse(strings, "mass")

    def test_massappct(self):
        strings = {
            "Commonwealth v. Forbes (AC 13-P-730) (August 26, 2014)": [
                "Commonwealth v. Forbes",
                "AC 13-P-730",
            ],
            "Commonwealth v. Malick (AC 09-P-1292, 11-P-0973) (August 25, 2014)": [
                "Commonwealth v. Malick",
                "AC 09-P-1292, 11-P-0973",
            ],
            "Litchfield's Case (AC 13-P-1044) (August 28, 2014)": [
                "Litchfield's Case",
                "AC 13-P-1044",
            ],
            "Rose v. Highway Equipment Company (AC 13-P-1215) (August 27, 2014)": [
                "Rose v. Highway Equipment Company",
                "AC 13-P-1215",
            ],
            "Commonwealth v. Alves (AC 13-P-1183) (August 27, 2014)": [
                "Commonwealth v. Alves",
                "AC 13-P-1183",
            ],
            "Commonwealth v. Dale (AC 12-P-1909) (August 25, 2014)": [
                "Commonwealth v. Dale",
                "AC 12-P-1909",
            ],
            "Kewley v. Department of Elementary and Secondary Education (AC 13-P-0833) (August 22, 2014)": [
                "Kewley v. Department of Elementary and Secondary Education",
                "AC 13-P-0833",
            ],
            "Hazel's Cup & Saucer, LLC v. Around The Globe Travel, Inc. (AC 13-P-1371) (August 22, 2014)": [
                "Hazel's Cup & Saucer, LLC v. Around The Globe Travel, Inc.",
                "AC 13-P-1371",
            ],
            "Becker v. Phelps (AC 13-P-0951) (August 22, 2014)": [
                "Becker v. Phelps",
                "AC 13-P-0951",
            ],
            "Barrow v. Dartmouth House Nursing Home, Inc. (AC 13-P-1375) (August 18, 2014)": [
                "Barrow v. Dartmouth House Nursing Home, Inc.",
                "AC 13-P-1375",
            ],
            "Zimmerling v. Affinity Financial Corp. (AC 13-P-1439) (August 18, 2014)": [
                "Zimmerling v. Affinity Financial Corp.",
                "AC 13-P-1439",
            ],
            "Lowell v. Talcott (AC 13-P-1053) (August 18, 2014)": [
                "Lowell v. Talcott",
                "AC 13-P-1053",
            ],
            "Copley Place Associates, LLC v. Tellez-Bortoni (AC 16-P-165) (January 01, 2017)": [
                "Copley Place Associates, LLC v. Tellez-Bortoni",
                "AC 16-P-165",
            ],
        }
        self.validate_mass_string_parse(strings, "massappct")

    def validate_mass_string_parse(self, strings, site_id):
        """Non-test method"""
        if site_id not in ["mass", "massappct"]:
            self.fail(
                "You provided an invalid site string to validate_mass_string_parse: %s"
                % site_id
            )
        site = mass.Site() if site_id == "mass" else massappct.Site()
        for raw_string, parsed in list(strings.items()):
            # Set year on site scraper
            site.year = int(raw_string.split(" ")[-1].rstrip(")"))
            site.set_local_variables()
            try:
                # make sure name is parsed
                self.assertEqual(
                    site.grouping_regex.search(raw_string).group(1).strip(),
                    parsed[0],
                )
                # make sure docket is parsed
                self.assertEqual(
                    site.grouping_regex.search(raw_string).group(2).strip(),
                    parsed[1],
                )
            except AttributeError:
                self.fail(
                    "Unable to parse %s string: '%s'" % (site_id, raw_string)
                )

    def test_nh(self):
        """Ensures regex parses what we think it should."""
        string_pairs = (
            (
                "2012-644, State of New Hampshire v. Adam Mueller",
                "State of New Hampshire v. Adam Mueller",
            ),
            (
                "2012-920, In re Trevor G.",
                "In re Trevor G.",
            ),
            (
                "2012-313, State of New Hampshire v. John A. Smith",
                "State of New Hampshire v. John A. Smith",
            ),
            (
                "2012-729, Appeal of the Local Government Center, Inc. & a . ",
                "Appeal of the Local Government Center, Inc. & a .",
            ),
            (
                "2013-0343  In the Matter of Susan Spenard and David Spenard",
                "In the Matter of Susan Spenard and David Spenard",
            ),
            (
                "2013-0893, Stephen E. Forster d/b/a Forster’s Christmas Tree",
                "Stephen E. Forster d/b/a Forster’s Christmas Tree",
            ),
        )
        regex = nh.Site().link_text_regex
        for test, result in string_pairs:
            try:
                case_name = regex.search(test).group(2).strip()
                self.assertEqual(
                    case_name,
                    result,
                    msg="Did not get expected results when regex'ing: '%s'.\n"
                    "  Expected: '%s'\n"
                    "  Instead:  '%s'" % (test, result, case_name),
                )
            except AttributeError:
                self.fail("Unable to parse nh string: '{s}'".format(s=test))

    def test_colo_coloctapp(self):
        """Ensures colo/coloctapp regex parses what we think it should."""
        tests = {
            "2016 COA 38. Nos. 14CA2454, 14CA2455, 14CA2456 & 14CA1457. People in the Interest of E.M.": {
                "docket": "14CA2454, 14CA2455, 14CA2456, 14CA1457",
                "name": "People in the Interest of E.M",
            },
            "2016 COA 32. No. 14CA1424. Brooks, Jr. v. Raemisch.": {
                "docket": "14CA1424",
                "name": "Brooks, Jr. v. Raemisch",
            },
            "2016 COA 33. Nos. 14CA1483 & 15CA0216. Rocky Mountain Exploration, Inc. v. Davis Graham & Stubbs LLP. ": {
                "docket": "14CA1483, 15CA0216",
                "name": "Rocky Mountain Exploration, Inc. v. Davis Graham & Stubbs LLP",
            },
            "2016 COA 79. 14CA2487. People v. Fransua.": {
                "docket": "14CA2487",
                "name": "People v. Fransua",
            },
            "2016 COA 51. No. 14CA2073.Campaign Integrity Watchdog v. Coloradans for a Better Future.": {
                "docket": "14CA2073",
                "name": "Campaign Integrity Watchdog v. Coloradans for a Better Future",
            },
            "2016 CO 43. No. 14SC1. Martinez v. Mintz.": {
                "docket": "14SC1",
                "name": "Martinez v. Mintz",
            },
            "No. 2016 COA 137. 15CA0620. Edwards v. Colorado Department of Revenue, Motor Vehicle Division. ": {
                "docket": "15CA0620",
                "name": "Edwards v. Colorado Department of Revenue, Motor Vehicle Division",
            }
            #'': {
            #    'docket': '',
            #    'name': '',
            # },
        }

        scraper = colo.Site()
        for raw_string, data in list(tests.items()):
            for field in ["docket", "name"]:
                attribute = "_extract_%s_from_text" % field
                result = getattr(scraper, attribute)(raw_string)
                self.assertEqual(
                    data[field],
                    result,
                    msg="Did not get expected %s results when regex'ing: '%s'.\n  Expected: '%s'\n  Instead:  '%s'"
                    % (field, raw_string, data[field], result),
                )

    def test_ca6_oa(self):
        # Tests are triads. 1: Input s, 2: Group 1, 3: Group 2.
        tests = (
            (
                "13-4101 Avis Rent A Car V City of Dayton Ohio",
                "13-4101",
                "Avis Rent A Car V City of Dayton Ohio",
            ),
            (
                "13-3950 13-3951 USA v Damien Russ",
                "13-3950 13-3951",
                "USA v Damien Russ",
            ),
            ("09 5517  USA vs Taylor", "09 5517", "USA vs Taylor"),
            ("11-2451Spikes v Mackie", "11-2451", "Spikes v Mackie"),
        )
        regex = ca6.Site().regex
        for test, group_1, group_2 in tests:
            try:
                result_1 = regex.search(test).group(1).strip()
                self.assertEqual(
                    result_1,
                    group_1,
                    msg="Did not get expected results when regex'ing: '%s'.\n"
                    "  Expected: '%s'\n"
                    "  Instead:  '%s'" % (test, group_1, result_1),
                )
                result_2 = regex.search(test).group(2).strip()
                self.assertEqual(
                    result_2,
                    group_2,
                    msg="Did not get expected results when regex'ing: '%s'.\n"
                    "  Expected: '%s'\n"
                    "  Instead:  '%s'" % (test, group_2, result_2),
                )
            except AttributeError:
                self.fail("Unable to parse ca6 string: '{s}'".format(s=test))
