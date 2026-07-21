import unittest
from datetime import date

from juriscraper.pacer import ACMSAttachmentPage
from tests.network import SKIP_IF_NO_PACER_LOGIN, get_pacer_session


class AcmsAttachmentPageTest(unittest.IsolatedAsyncioTestCase):
    """A test of basic info for the Case Query"""

    async def asyncSetUp(self):
        self.session = get_pacer_session()
        await self.session.login()
        self.report = ACMSAttachmentPage("ca2", self.session)
        self.pacer_case_id = "70c4875d-f112-48e5-ad41-5e6d403ca9cd"  # Ogunbekun v. Town of Brighton
        self.docket_doc_id = (
            "21ad9f34-6350-f011-877a-001dd803d067"  # Docket Entry 7
        )

    @SKIP_IF_NO_PACER_LOGIN
    async def test_queries(self):
        """Do a variety of queries work?"""
        await self.report.query(self.pacer_case_id, self.docket_doc_id)
        data = self.report.data

        self.assertEqual(
            7,
            data["entry_number"],
            msg="entry number query failed",
        )
        self.assertIn(
            "MOTION, to be relieved as counsel, on behalf of Appellant Ibukun Ogunbekun",
            data["description"],
            msg="description query failed",
        )
        self.assertEqual(
            date(2025, 6, 23),
            data["date_filed"],
            msg="date_filed query failed",
        )
        self.assertEqual(
            date(2025, 6, 23),
            data["date_end"],
            msg="appeal_from query failed",
        )
        self.assertIsNotNone(
            data["attachments"], msg="attachments query failed"
        )
        self.assertEqual(
            3, len(data["attachments"]), msg="attachments count query failed"
        )
