#!/usr/bin/env python


import fnmatch
import json
import os
import sys
import unittest

from juriscraper.lib.exceptions import ParsingException
from juriscraper.pacer import PossibleCaseNumberApi
from tests import TESTS_ROOT_EXAMPLES_PACER


class PacerPossibleCaseNumbersTest(unittest.TestCase):
    def setUp(self):
        xml = """
            <request number="16-01152">
                <case number="1:16-cr-1152" id="1000068"
                      title="1:16-cr-01152-JZB USA v. Abuarar (closed 01/26/2017)"
                      sortable="1:2016-cr-01152"/>

                <!-- For use with office and case name filtering -->
                <case number="2:16-cv-1152" id="977547"
                      title="2:16-cv-01152-JJT Willy Wonka v. Charlie (closed 06/09/2017)"
                      sortable="2:2016-cv-01152-JJT"/>
                <case number="2:16-cr-1152" id="977548"
                      title="2:16-cv-01152-JJT Armes v. Hot Pizzas LLC (closed 06/09/2017)"
                      sortable="2:2016-cv-01152-JJT"/>

                <!-- Not non-sequential id values -->
                <case number="3:16-cr-1152" id="1"
                      title="3:16-cr-01152-JJT Willy Wonka v. Charlie (closed 06/09/2017)"
                      sortable="3:2016-cr-01152-JJT"/>
                <case number="3:16-cr-1152" id="3"
                      title="3:16-cv-01152-JJT Armes v. Hot Pizzas LLC (closed 06/09/2017)"
                      sortable="3:2016-cv-01152-JJT"/>
            </request>
        """
        self.report = PossibleCaseNumberApi("anything")
        self.report._parse_text(xml)

    def test_parsing_results(self):
        """Can we do a simple query and parse?"""
        paths = []
        path_root = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "possible_case_numbers"
        )
        for root, _, filenames in os.walk(path_root):
            for filename in fnmatch.filter(filenames, "*.xml"):
                paths.append(os.path.join(root, filename))
        paths.sort()
        path_max_len = max(len(path) for path in paths) + 2
        for i, path in enumerate(paths):
            sys.stdout.write(f"{i}. Doing {path.ljust(path_max_len)}")
            dirname, filename = os.path.split(path)
            filename_sans_ext = filename.split(".")[0]
            json_path = os.path.join(dirname, f"{filename_sans_ext}.json")

            report = PossibleCaseNumberApi("anything")
            with open(path, "rb") as f:
                report._parse_text(f.read().decode("utf-8"))
            data = report.data(case_name=filename_sans_ext)
            if os.path.exists(json_path):
                with open(json_path) as f:
                    j = json.load(f)
                    self.assertEqual(j, data)
            else:
                # If no json file, data should be None.
                if data is not None:
                    with open(json_path, "w") as f:
                        print(f"Creating new file at {json_path}")
                        json.dump(data, f, indent=2, sort_keys=True)
                else:
                    self.assertIsNone(
                        data,
                        msg="No json file detected and response is not None. "
                        "Either create a json file for this test or make sure "
                        "you get back valid results.",
                    )

            sys.stdout.write("✓\n")

    def test_filtering_by_office_number(self):
        """Can we filter by office number?"""
        d = self.report.data(office_number="1")
        self.assertEqual("1000068", d["pacer_case_id"])

    def test_filtering_by_civil_or_criminal(self):
        """Can we filter by civil or criminal?"""
        d = self.report.data(docket_number_letters="cv")
        self.assertEqual("977547", d["pacer_case_id"])

    def test_filtering_by_office_and_civil_criminal(self):
        """Can we filter by multiple variables?"""
        d = self.report.data(
            office_number="2",
            docket_number_letters="cr",
        )
        self.assertEqual("977548", d["pacer_case_id"])

    def test_filtering_by_case_name(self):
        d = self.report.data(case_name="Willy Wonka")
        self.assertEqual("977547", d["pacer_case_id"])

    def test_filtering_by_office_and_case_name(self):
        d = self.report.data(office_number="2", case_name="Willy Wonka")
        self.assertEqual("977547", d["pacer_case_id"])

    def test_choosing_the_lowest_sequentially(self):
        """When the ids are sequential, can we pick the lowest one?"""
        d = self.report.data(office_number="2")
        self.assertEqual("977547", d["pacer_case_id"])

    def test_cannot_make_choice_because_not_sequential_ids(self):
        """When the remaining nodes only have IDs that aren't sequential, do we
        give up and throw an error?
        """
        with self.assertRaises(ParsingException):
            _ = self.report.data(office_number="3")

    def test_no_case_name_with_sequential_ids(self):
        """Does this work properly when we don't have a case name, but we do
        have the office number, criminal vs. civil info, and sequential ids?
        """
        xml = """
        <request number='1700355'>
            <case number='3:17-cv-355' id='307135'
                  title='3:17-cv-00355-MEJ Emeziem v. JPMorgan Chase Bank, N.A. (closed 11/09/2017)'
                  sortable='3:2017-cv-00355-MEJ'/>
            <case number='4:17-cr-355' id='313707'
                  title='4:17-cr-00355-YGR USA v. Kim et al' defendant='0'
                  sortable='4:2017-cr-00355-YGR'/>
            <case number='4:17-cr-355-1' id='313708'
                  title='4:17-cr-00355-YGR-1 Man Young Kim' defendant='1'
                  sortable='4:2017-cr-00355'/>
            <case number='4:17-cr-355-2' id='313709'
                  title='4:17-cr-00355-YGR-2 Kyong Ja Kim' defendant='2'
                  sortable='4:2017-cr-00355'/>
        </request>
        """
        report = PossibleCaseNumberApi("anything")
        report._parse_text(xml)
        d = report.data(office_number="4", docket_number_letters="cr")
        self.assertEqual("313707", d["pacer_case_id"])

    def test_pick_sequentially_by_defendant_number(self):
        """Does this work properly when we pick by sequential defendant number?"""
        xml = """
        <request number='1700355'>
            <case number='2:15-cr-158'   id='284385'
                  title='2:15-cr-00158-JAM USA v. Beaver et al (closed 12/12/2017)'
                  defendant='0' sortable='2:2015-cr-00158-JAM'/>
            <case number='2:15-cr-158-1' id='285846'
                  title='2:15-cr-00158-JAM-1 Bryce Beaver (closed 05/24/2016)'
                  defendant='1' sortable='2:2015-cr-00158'/>
            <case number='2:15-cr-158-2' id='284386'
                  title='2:15-cr-00158-JAM-2 Charles Beaver (closed 10/18/2016)'
                  defendant='2' sortable='2:2015-cr-00158'/>
            <case number='2:15-cr-158-3' id='284858'
                  title='2:15-cr-00158-JAM-3 Sharod Gibbons (closed 12/12/2017)'
                  defendant='3' sortable='2:2015-cr-00158'/>
        </request>
        """
        report = PossibleCaseNumberApi("anything")
        report._parse_text(xml)
        d = report.data()
        self.assertEqual("284385", d["pacer_case_id"])
