from __future__ import print_function

import os
import unittest

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


class PacerDocketReportTest(unittest.TestCase):
    """A variety of tests for the docket report"""

    def setUp(self):
        pacer_session = PacerSession(username=PACER_USERNAME,
                                     password=PACER_PASSWORD)
        pacer_session.login()
        self.report = DocketReport('cand', pacer_session)
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
    def test_using_same_report_twice(self):
        """Do the caches get properly nuked between runs?

        See issue #187.
        """
        # Query the first one...
        self.report.query(self.pacer_case_id)
        d = self.report.data.copy()

        # Then the second one...
        second_pacer_case_id = '63111'  # 1:07-cv-00035-RJA-HKS Anson v. USA
        self.report.query(second_pacer_case_id)
        d2 = self.report.data.copy()
        self.assertNotEqual(
            d,
            d2,
            msg="Got same values for docket data of two different queries. "
                "Is there a problem with the caches on the DocketReport?"
        )
