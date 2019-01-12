from __future__ import print_function

import os
import time
import unittest
from datetime import date

from juriscraper.lib.html_utils import get_html_parsed_text
from juriscraper.pacer import DocketReport
from juriscraper.pacer.http import PacerSession

PACER_USERNAME = os.environ.get('PACER_USERNAME', None)
PACER_PASSWORD = os.environ.get('PACER_PASSWORD', None)
PACER_SETTINGS_MSG = "Skipping test. Please set PACER_USERNAME and " \
                     "PACER_PASSWORD environment variables to run this test."
SKIP_IF_NO_PACER_LOGIN = unittest.skipUnless(
    (PACER_USERNAME and PACER_PASSWORD),
    reason=PACER_SETTINGS_MSG)


class AuthTest(unittest.TestCase):
    """Test logging in twice."""

    @staticmethod
    def _count_rows(html):
        """Count the rows in the docket report.

        :param html: The HTML of the docket report.
        :return: The count of the number of rows.
        """
        tree = get_html_parsed_text(html)
        return len(tree.xpath('//table[./tr/td[3]]/tr')) - 1  # No header row

    def test_double_auth(self):
        s = PacerSession(username=PACER_USERNAME, password=PACER_PASSWORD)
        s.login()
        s.login()
        report = DocketReport('cand', s)
        report.query('186730', date_start=date(2007, 11, 1))
        row_count = self._count_rows(report.response.text)
        self.assertEqual(2, row_count, msg="Didn't get expected number of "
                                           "rows when filtering by start "
                                           "date. Got %s." % row_count)


class PacerDocketReportTest(unittest.TestCase):
    """A variety of tests for the docket report"""

    pacer_session = PacerSession(username=PACER_USERNAME,
                                 password=PACER_PASSWORD)
    pacer_session.login()

    def setUp(self):
        self.report = DocketReport('cand', self.pacer_session)
        self.pacer_case_id = '186730'  # 4:06-cv-07294 Foley v. Bates

    @staticmethod
    def _count_rows(html):
        """Count the rows in the docket report.

        :param html: The HTML of the docket report.
        :return: The count of the number of rows.
        """
        tree = get_html_parsed_text(html)
        return len(tree.xpath('//table[./tr/td[3]]/tr')) - 1  # No header row

    @SKIP_IF_NO_PACER_LOGIN
    def test_queries(self):
        """Do a variety of queries work?"""
        # self.report.query(self.pacer_case_id)
        # self.assertIn('Foley v. Bates', self.report.response.text,
        #               msg="Super basic query failed")
        #
        # self.pacer_session.login()
        # self.report = DocketReport('cand', self.pacer_session)
        time.sleep(1)
        self.report.query(self.pacer_case_id, date_start=date(2007, 11, 1))
        row_count = self._count_rows(self.report.response.text)
        self.assertEqual(2, row_count, msg="Didn't get expected number of "
                                           "rows when filtering by start "
                                           "date. Got %s." % row_count)

        time.sleep(1)
        self.report.query(self.pacer_case_id, date_start=date(2007, 11, 1),
                          date_end=date(2007, 11, 28))
        row_count = self._count_rows(self.report.response.text)
        self.assertEqual(1, row_count, msg="Didn't get expected number of "
                                           "rows when filtering by start and "
                                           "end dates. Got %s." % row_count)
        time.sleep(1)
        self.report.query(self.pacer_case_id, doc_num_start=5,
                          doc_num_end=5)
        row_count = self._count_rows(self.report.response.text)
        self.assertEqual(1, row_count,
                         msg="Didn't get expected number of rows "
                             "when filtering by doc number. Got "
                             "%s" % row_count)
        time.sleep(1)
        self.report.query(self.pacer_case_id, date_start=date(2007, 11, 1),
                          date_end=date(2007, 11, 28),
                          date_range_type="Entered")
        row_count = self._count_rows(self.report.response.text)
        self.assertEqual(1, row_count,
                         msg="Didn't get expected number of rows "
                             "when filtering by start and end "
                             "dates and date_range_type of "
                             "Entered. Got %s" % row_count)
        time.sleep(1)
        self.report.query(self.pacer_case_id, doc_num_start=500,
                          show_parties_and_counsel=True)
        self.assertIn('Cheema', self.report.response.text,
                      msg="Didn't find party info when it was explicitly "
                          "requested.")
        time.sleep(1)
        self.report.query(self.pacer_case_id, doc_num_start=500,
                          show_parties_and_counsel=False)
        self.assertNotIn('Cheema', self.report.response.text,
                         msg="Got party info but it was not requested.")

    # @SKIP_IF_NO_PACER_LOGIN
    # def test_using_same_report_twice(self):
    #     """Do the caches get properly nuked between runs?
    #
    #     See issue #187.
    #     """
    #     # Query the first one...
    #     self.report.query(self.pacer_case_id)
    #     d = self.report.data.copy()
    #
    #     # Then the second one...
    #     second_pacer_case_id = '63111'  # 1:07-cv-00035-RJA-HKS Anson v. USA
    #     self.report.query(second_pacer_case_id)
    #     d2 = self.report.data.copy()
    #     self.assertNotEqual(
    #         d,
    #         d2,
    #         msg="Got same values for docket data of two different queries. "
    #             "Is there a problem with the caches on the DocketReport?"
    #     )
