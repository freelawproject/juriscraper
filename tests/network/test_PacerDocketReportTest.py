#!/usr/bin/env python


import unittest
from datetime import date

from juriscraper.lib.html_utils import get_html_parsed_text
from juriscraper.pacer import DocketReport
from tests.network import SKIP_IF_NO_PACER_LOGIN, get_pacer_session


class PacerDocketReportTest(unittest.IsolatedAsyncioTestCase):
    """A variety of tests for the docket report"""

    async def asyncSetUp(self):
        self.session = get_pacer_session()
        await self.session.login()
        self.report = DocketReport("cand", self.session)
        self.pacer_case_id = "186730"  # 4:06-cv-07294 Foley v. Bates

    @staticmethod
    def _count_rows(html):
        """Count the rows in the docket report.

        :param html: The HTML of the docket report.
        :return: The count of the number of rows.
        """
        tree = get_html_parsed_text(html)
        return len(tree.xpath("//table[./tr/td[3]]/tr")) - 1  # No header row

    @SKIP_IF_NO_PACER_LOGIN
    async def test_queries(self):
        """Do a variety of queries work?"""
        await self.report.query(self.pacer_case_id)
        self.assertIn(
            "Foley v. Bates",
            self.report.response.text,
            msg="Super basic query failed",
        )

        await self.report.query(
            self.pacer_case_id, date_start=date(2007, 11, 1)
        )
        row_count = self._count_rows(self.report.response.text)
        self.assertEqual(
            2,
            row_count,
            msg="Didn't get expected number of "
            "rows when filtering by start "
            "date. Got %s." % row_count,
        )

        await self.report.query(
            self.pacer_case_id,
            date_start=date(2007, 11, 1),
            date_end=date(2007, 11, 28),
        )
        row_count = self._count_rows(self.report.response.text)
        self.assertEqual(
            1,
            row_count,
            msg="Didn't get expected number of "
            "rows when filtering by start and "
            "end dates. Got %s." % row_count,
        )

        await self.report.query(
            self.pacer_case_id, doc_num_start=5, doc_num_end=5
        )
        row_count = self._count_rows(self.report.response.text)
        self.assertEqual(
            1,
            row_count,
            msg="Didn't get expected number of rows "
            "when filtering by doc number. Got "
            "%s" % row_count,
        )

        await self.report.query(
            self.pacer_case_id,
            date_start=date(2007, 11, 1),
            date_end=date(2007, 11, 28),
            date_range_type="Entered",
        )
        row_count = self._count_rows(self.report.response.text)
        self.assertEqual(
            1,
            row_count,
            msg="Didn't get expected number of rows "
            "when filtering by start and end "
            "dates and date_range_type of "
            "Entered. Got %s" % row_count,
        )

        await self.report.query(
            self.pacer_case_id,
            doc_num_start=500,
            show_parties_and_counsel=True,
        )
        self.assertIn(
            "Cheema",
            self.report.response.text,
            msg="Didn't find party info when it was explicitly requested.",
        )
        await self.report.query(
            self.pacer_case_id,
            doc_num_start=500,
            show_parties_and_counsel=False,
        )
        self.assertNotIn(
            "Cheema",
            self.report.response.text,
            msg="Got party info but it was not requested.",
        )

    @SKIP_IF_NO_PACER_LOGIN
    async def test_using_same_report_twice(self):
        """Do the caches get properly nuked between runs?

        See issue #187.
        """
        # Query the first one...
        await self.report.query(self.pacer_case_id)
        d = self.report.data.copy()

        # Then the second one...
        second_pacer_case_id = "63111"  # 1:07-cv-00035-RJA-HKS Anson v. USA
        await self.report.query(second_pacer_case_id)
        d2 = self.report.data.copy()
        self.assertNotEqual(
            d,
            d2,
            msg="Got same values for docket data of two different queries. "
            "Is there a problem with the caches on the DocketReport?",
        )
