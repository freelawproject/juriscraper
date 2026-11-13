import unittest
from unittest import mock

from juriscraper.pacer import ACMSDocketReport


class ACMSDocketReportQueryByDocketNumberTest(
    unittest.IsolatedAsyncioTestCase
):
    """Test looking an ACMS docket up by its docket number."""

    CASE_DETAILS = {
        "caseId": "481e75a0-8940-46d4-bb54-1135c0b4b34b",
        "caseNumber": "26-7519",
        "name": "Collins v. Spotify USA, Inc., et al.",
        "caseOpened": "2026-11-10T00:00:00",
        "aNumber": None,
        "receivedDate": "2026-11-10T09:34:20Z",
        "partyAttorneyList": (
            "<table><tr><td>ERIC DWAYNE COLLINS<br>Plaintiff - Appellant"
            "<td>pro se</table>"
        ),
        "shortCaption": "COLLINS v. SPOTIFY USA, INC.",
        "court": {
            "name": "Los Angeles, Central California",
            "abbreviatedName": "Central District of California",
        },
        "caseType": "Civil",
        "caseSubType": "Private",
        "caseSubSubType": None,
        "districtCourtName": None,
        "feeStatus": "Paid",
    }
    DOCKET_INFO = {
        "docketEntries": [
            {
                "endDate": "2026-11-10",
                "endDateFormatted": "11/10/2026",
                "entryNumber": 1,
                "docketEntryText": "<p>DOCKETED CAUSE. [Entered: 11/10/2026 9:34 AM]</p>",
                "docketEntryId": "19b65316-744e-11ee-a0a4-13890013fe63",
                "pageCount": 2,
            }
        ]
    }

    def setUp(self):
        self.report = ACMSDocketReport("ca9", pacer_session=mock.MagicMock())
        self.index_content = mock.patch.object(
            self.report.api_client, "get_index_content"
        ).start()
        self.docket_entries = mock.patch.object(
            self.report.api_client, "get_docket_entries"
        ).start()
        self.addCleanup(mock.patch.stopall)

    async def test_entries_come_from_the_page_when_present(self):
        """A page carrying docket entries needs no API call."""
        self.index_content.return_value = {
            "caseDetails": [self.CASE_DETAILS],
            "docketInfo": self.DOCKET_INFO,
        }

        await self.report.query_by_docket_number("26-7519")

        self.index_content.assert_awaited_once_with("26-7519")
        self.docket_entries.assert_not_awaited()
        data = self.report.data
        self.assertEqual(data["pacer_case_id"], self.CASE_DETAILS["caseId"])
        self.assertEqual(data["docket_number"], "26-7519")
        self.assertEqual(data["case_name"], self.CASE_DETAILS["name"])
        self.assertEqual(
            data["appeal_from"], "Los Angeles, Central California"
        )
        self.assertEqual(len(data["docket_entries"]), 1)
        self.assertEqual(data["docket_entries"][0]["document_number"], 1)

    async def test_entries_fetched_from_api_when_page_has_none(self):
        """Without entries on the page, the API supplies them by case id."""
        self.index_content.return_value = {"caseDetails": [self.CASE_DETAILS]}
        self.docket_entries.return_value = self.DOCKET_INFO

        await self.report.query_by_docket_number("26-7519")

        self.docket_entries.assert_awaited_once_with(
            self.CASE_DETAILS["caseId"]
        )
        self.assertEqual(len(self.report.data["docket_entries"]), 1)

    async def test_unknown_docket_number_gives_empty_data(self):
        """No case for the number means empty data and no further requests."""
        self.index_content.return_value = {"caseDetails": []}

        await self.report.query_by_docket_number("99-9999")

        self.docket_entries.assert_not_awaited()
        self.assertEqual(self.report.data, {})

    async def test_requires_session(self):
        """A report without a session cannot query."""
        report = ACMSDocketReport("ca9")
        with self.assertRaises(AssertionError):
            await report.query_by_docket_number("26-7519")
