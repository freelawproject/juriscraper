import unittest
from datetime import date

from juriscraper.pacer import ACMSDocketReport
from tests.network import SKIP_IF_NO_PACER_LOGIN, get_pacer_session


class AcmsDocketReportTest(unittest.TestCase):
    """A test of basic info for the Case Query"""

    def setUp(self):
        self.session = get_pacer_session()
        self.session.login()
        self.report = ACMSDocketReport("ca2", self.session)
        self.pacer_case_id = "ee86bf29-5e50-f011-a2da-001dd8307a8d"  # Partners Agency Services, LLC v. LaMonica

    @SKIP_IF_NO_PACER_LOGIN
    def test_queries(self):
        """Do a variety of queries work?"""
        self.report.query(self.pacer_case_id)
        metadata = self.report.metadata
        self.assertIn(
            "25-1569",
            metadata["docket_number"],
            msg="docket_number query failed",
        )
        self.assertEqual(
            "Patriarch Partners Agency Services, LLC v. LaMonica",
            metadata["case_name"],
            msg="case_name query failed",
        )
        self.assertEqual(
            date(2025, 6, 24),
            metadata["date_filed"],
            msg="date_filed query failed",
        )
        self.assertEqual(
            "SDNY (NEW YORK CITY)",
            metadata["appeal_from"],
            msg="appeal_from query failed",
        )
        self.assertEqual(
            "Not Applicable",
            metadata["fee_status"],
            msg="fee_status query failed",
        )

        self.assertIsNotNone(self.report.parties)
        self.assertIsNotNone(self.report.docket_entries)
