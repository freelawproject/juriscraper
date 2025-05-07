#!/usr/bin/env python


import unittest
from datetime import date

from juriscraper.pacer import CaseQuery
from tests.network import SKIP_IF_NO_PACER_LOGIN, get_pacer_session


class PacerCaseQueryTest(unittest.TestCase):
    """A test of basic info for the Case Query"""

    def setUp(self):
        self.session = get_pacer_session()
        self.session.login()
        self.report = CaseQuery("cand", self.session)
        self.pacer_case_id = "186730"  # 4:06-cv-07294 Foley v. Bates

    @SKIP_IF_NO_PACER_LOGIN
    def test_query(self):
        """Can we get the basic info?"""
        self.report.query(self.pacer_case_id)
        self.assertIn(
            "Foley v. Bates",
            self.report.response.text,
            msg="Super basic query failed",
        )

        metadata = self.report.metadata
        self.assertIn(
            "Foley v. Bates et al",
            metadata["case_name_raw"],
            msg="case_name_raw query failed",
        )
        self.assertEqual(
            date(2007, 11, 29),
            metadata["date_last_filing"],
            msg="date_last_filing query failed",
        )
        self.assertEqual(
            date(2007, 5, 7),
            metadata["date_terminated"],
            msg="date_terminated query failed",
        )
        self.assertEqual(
            date(2006, 11, 27),
            metadata["date_filed"],
            msg="date_filed query failed",
        )
