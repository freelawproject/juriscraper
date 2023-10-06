#!/usr/bin/env python
import asyncio
import os
import unittest
from datetime import date, timedelta
from unittest import mock

import jsondate3 as json
from httpx import ConnectError

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.pacer import DownloadConfirmationPage, FreeOpinionReport
from juriscraper.pacer.http import PacerSession
from juriscraper.pacer.utils import get_court_id_from_url, get_courts_from_json
from tests import JURISCRAPER_ROOT, TESTS_ROOT_EXAMPLES_PACER
from tests.network import (
    SKIP_IF_NO_PACER_LOGIN,
    get_pacer_session,
    pacer_credentials_are_defined,
)


class PacerFreeOpinionsTest(unittest.IsolatedAsyncioTestCase):
    """A variety of tests relating to the Free Written Opinions report"""

    async def asyncSetUp(self):
        pacer_session = PacerSession()

        if pacer_credentials_are_defined():
            # CAND chosen at random
            pacer_session = get_pacer_session()
            await pacer_session.login()

        with open(os.path.join(JURISCRAPER_ROOT, "pacer/courts.json")) as j:
            self.courts = get_courts_from_json(json.load(j))

        path = os.path.join(
            TESTS_ROOT_EXAMPLES_PACER, "dates/valid_free_opinion_dates.json"
        )
        with open(path) as j:
            self.valid_dates = json.load(j)

        self.reports = {}
        for court in self.courts:
            court_id = get_court_id_from_url(court["court_link"])
            self.reports[court_id] = FreeOpinionReport(court_id, pacer_session)

    @unittest.skip("disabling during refactor")
    async def test_extract_written_documents_report(self):
        """Do all the written reports work?"""

        for court in self.courts:
            if court["type"] == "U.S. Courts of Appeals":
                continue
            court_id = get_court_id_from_url(court["court_link"])

            if court_id not in self.valid_dates:
                continue

            results = []
            report = self.reports[court_id]
            some_date = convert_date_string(self.valid_dates[court_id])
            retry_count = 1
            max_retries = 5  # We'll try five times total
            while not results and retry_count <= max_retries:
                # This loop is sometimes needed to find a date with documents.
                # In general the valid dates json object should suffice,
                # however.
                if some_date > date.today():
                    raise ValueError(
                        f"Runaway date query for {court_id}: {some_date}"
                    )
                try:
                    await report.query(
                        some_date, some_date, sort="case_number"
                    )
                except ConnectError as e:
                    if retry_count <= max_retries:
                        print(
                            "%s. Trying again (%s of %s)"
                            % (e, retry_count, max_retries)
                        )
                        await asyncio.sleep(
                            10
                        )  # Give the server a moment of rest.
                        retry_count += 1
                        continue
                    else:
                        print(f"{e}: Repeated errors at this court.")
                        raise e
                if not report.responses:
                    break  # Not a supported court.
                some_date += timedelta(days=1)

            else:
                # While loop ended normally (without hitting break)
                for result in results:
                    for k, v in result.items():
                        if k in ["nature_of_suit", "cause"]:
                            continue
                        self.assertIsNotNone(
                            v,
                            msg="Value of key %s is None in court %s"
                            % (k, court_id),
                        )

                # Can we download one item from each court?
                r, msg = await report.download_pdf(
                    results[0]["pacer_case_id"], results[0]["pacer_doc_id"]
                )
                if r is None:
                    # Extremely messed up download.
                    continue
                self.assertEqual(r.headers["Content-Type"], "application/pdf")

    @SKIP_IF_NO_PACER_LOGIN
    async def test_download_simple_pdf(self):
        """Can we download a PDF document returned directly?"""
        report = self.reports["alnb"]
        r, msg = await report.download_pdf("602431", "018129511556")
        self.assertEqual(r.headers["Content-Type"], "application/pdf")

    @SKIP_IF_NO_PACER_LOGIN
    async def test_download_redirected_pdf(self):
        """Can we download a PDF document returned after a redirection?"""
        report = self.reports["azd"]
        r, msg = await report.download_pdf("1311031", "025125636132")
        self.assertEqual(r.headers["Content-Type"], "application/pdf")

    @SKIP_IF_NO_PACER_LOGIN
    async def test_download_iframed_pdf(self):
        """Can we download a PDF document returned in IFrame?"""
        report = self.reports["vib"]
        r, msg = await report.download_pdf("1507", "1921141093")
        self.assertEqual(r.headers["Content-Type"], "application/pdf")

    @SKIP_IF_NO_PACER_LOGIN
    async def test_download_unavailable_pdf(self):
        """Do we throw an error if the item is unavailable?"""
        # 5:11-cr-40057-JAR, document 3
        report = self.reports["ksd"]
        r, msg = await report.download_pdf("81531", "07902639735")
        self.assertIsNone(r)
        self.assertIn("Document not available in case", msg)

    @SKIP_IF_NO_PACER_LOGIN
    async def test_query_can_get_multiple_results(self):
        """
        Can we run a query that gets multiple rows and parse them all?
        """
        court_id = "paeb"
        report = self.reports[court_id]
        some_date = convert_date_string(self.valid_dates[court_id])
        await report.query(some_date, some_date, sort="case_number")
        self.assertEqual(3, len(report.data), "should get 3 responses for ksb")

    @SKIP_IF_NO_PACER_LOGIN
    async def test_query_using_last_good_row(self):
        """
        Can we run a query that triggers no content in first cell?
        """
        court_id = "ksb"
        report = self.reports[court_id]
        some_date = convert_date_string(self.valid_dates[court_id])
        await report.query(some_date, some_date, sort="case_number")
        self.assertEqual(2, len(report.data), "should get 2 response for ksb")

    @SKIP_IF_NO_PACER_LOGIN
    async def test_ordering_by_date_filed(self):
        """Can we change the ordering?"""
        # First try both orderings in areb (where things have special cases) and
        # ded (Delaware) where things are more normal.
        tests = ({"court": "areb", "count": 1}, {"court": "ded", "count": 4})
        for test in tests:
            report = self.reports[test["court"]]
            some_date = convert_date_string(self.valid_dates[test["court"]])
            await report.query(some_date, some_date, sort="date_filed")
            self.assertEqual(
                test["count"],
                len(report.data),
                f"Should get {test['count']} response for {test['court']}",
            )
            await report.query(some_date, some_date, sort="case_number")
            self.assertEqual(
                test["count"],
                len(report.data),
                f"should get {test['count']} response for {test['court']}",
            )

    async def test_catch_excluded_court_ids(self):
        """Do we properly catch and prevent a query against disused courts?"""
        mock_session = mock.MagicMock()

        report = self.reports["casb"]
        report.session = mock_session

        some_date = convert_date_string("1/1/2015")

        await report.query(some_date, some_date, sort="case_number")
        self.assertEqual([], report.responses, "should have empty result set")
        self.assertFalse(
            mock_session.post.called, msg="should not trigger a POST query"
        )


@mock.patch("juriscraper.pacer.reports.logger")
class PacerMagicLinkTest(unittest.IsolatedAsyncioTestCase):
    """Test related to PACER magic link free download"""

    async def asyncSetUp(self):
        pacer_session = PacerSession()
        if pacer_credentials_are_defined():
            # CAND chosen at random
            pacer_session = get_pacer_session()
            await pacer_session.login()

        self.reports = {}
        court_id = "nysd"
        court_id_nda = "ca3"
        court_id_acms = "ca9"
        self.reports[court_id] = FreeOpinionReport(court_id, pacer_session)
        self.reports[court_id_nda] = FreeOpinionReport(
            court_id_nda, pacer_session
        )
        self.reports[court_id_acms] = FreeOpinionReport(
            court_id_acms, pacer_session
        )

    async def test_download_simple_pdf_magic_link_fails(self, mock_logger):
        """Can we download a PACER document with an invalid or expired
        magic link? land on a login page and returns an error.
        """
        report = self.reports["nysd"]
        url = "https://ecf.nysd.uscourts.gov/doc1/127130869087"
        pacer_case_id = "568350"
        pacer_doc_id = "127130869087"
        pacer_magic_num = "46253052"
        r, msg = await report.download_pdf(
            pacer_case_id, pacer_doc_id, pacer_magic_num
        )
        mock_logger.warning.assert_called_with(
            "Document not available via magic link in case: "
            f"caseid: {pacer_case_id}, magic_num: {pacer_magic_num}, "
            f"URL: {url}"
        )
        # No PDF should be returned
        self.assertEqual(r, None)

    async def test_download_nda_pdf_magic_link(self, mock_logger):
        """Can we download a NDA PACER document with an invalid or expired
        magic link? land on a login page and returns an error.
        """
        report = self.reports["ca3"]
        url = "https://ecf.ca3.uscourts.gov/docs1/003114193380"
        pacer_case_id = "21-1832"
        pacer_doc_id = "003014193380"
        pacer_magic_num = "3594681a19879633"
        appellate = True
        r, msg = await report.download_pdf(
            pacer_case_id, pacer_doc_id, pacer_magic_num, appellate
        )
        mock_logger.warning.assert_called_with(
            "Document not available via magic link in case: "
            f"caseid: {pacer_case_id}, magic_num: {pacer_magic_num}, "
            f"URL: {url}"
        )
        # No PDF should be returned
        self.assertEqual(r, None)

    async def test_download_acms_nda_pdf_magic_link(self, mock_logger):
        """Can we download an NDA ACMS PACER document with an invalid or expired
        magic link? land on a login page and returns an error.
        """
        report = self.reports["ca9"]
        url = "https://ca9-showdoc.azurewebsites.us/NDA/6b939b7c-9a69-f011-bec2-001dd806079d"
        pacer_magic_num = "6b939b7c-9a69-f011-bec2-001dd806079d"
        r, msg = await report.download_pdf(
            None, None, pacer_magic_num, acms=True
        )
        mock_logger.warning.assert_called_with(
            "Document not available via magic link in case: "
            f"caseid: {None}, magic_num: {pacer_magic_num}, "
            f"URL: {url}"
        )
        # No PDF should be returned
        self.assertEqual(r, None)


class PacerDownloadConfirmationPageTest(unittest.IsolatedAsyncioTestCase):
    """A variety of tests for the download confirmation page"""

    async def asyncSetUp(self):
        self.session = get_pacer_session()
        await self.session.login()
        self.report = DownloadConfirmationPage("ca8", self.session)
        self.report_att = DownloadConfirmationPage("ca5", self.session)
        self.report_pdf = DownloadConfirmationPage("ca11", self.session)
        self.report_nef_no_confirmation = DownloadConfirmationPage(
            "txwd", self.session
        )
        self.report_nef = DownloadConfirmationPage("cand", self.session)
        self.pacer_doc_id = "00812590792"
        self.no_confirmation_page_pacer_doc_id = "00802251695"
        self.pacer_doc_id_att = "00506470276"
        self.pacer_doc_id_pdf = "011012534985"
        self.pacer_doc_id_nef_no_confirmation = "181027895860"
        self.pacer_doc_id_nef = "035022812318"

    @SKIP_IF_NO_PACER_LOGIN
    async def test_get_document_number(self):
        """Can we get the PACER document number from a download confirmation
        page?"""
        await self.report.query(self.pacer_doc_id)
        data_report = self.report.data
        self.assertEqual(data_report["document_number"], "00812590792")
        self.assertEqual(data_report["docket_number"], "14-3066")
        self.assertEqual(data_report["cost"], "0.30")
        self.assertEqual(data_report["billable_pages"], "3")
        self.assertEqual(data_report["document_description"], "PDF Document")

    @SKIP_IF_NO_PACER_LOGIN
    async def test_get_document_number_skipping_attachment_page(self):
        """Can we get the PACER document number from a download confirmation
        page skipping the attachment page?"""
        await self.report_att.query(self.pacer_doc_id_att)
        data_report = self.report_att.data
        self.assertEqual(data_report["document_number"], "45-1")
        self.assertEqual(data_report["docket_number"], "22-30311")
        self.assertEqual(data_report["cost"], "1.50")
        self.assertEqual(data_report["billable_pages"], "15")
        self.assertEqual(data_report["document_description"], "PDF Document")

    @SKIP_IF_NO_PACER_LOGIN
    async def test_no_confirmation_page(self):
        """If the download confirmation page is not available an empty
        dictionary is returned"""
        await self.report.query(self.no_confirmation_page_pacer_doc_id)
        data_report = self.report.data
        self.assertEqual(data_report, {})

    @SKIP_IF_NO_PACER_LOGIN
    async def test_no_confirmation_page_pdf_returned(self):
        """If the download confirmation page is not available when the PDF is
        returned directly, no valid page to parse."""
        await self.report_pdf.query(self.pacer_doc_id_pdf)
        data_report = self.report_pdf.data
        self.assertEqual(data_report, {})

    @SKIP_IF_NO_PACER_LOGIN
    async def test_confirmation_page_pdf_district(self):
        """Can we get the PACER document number from a district download
        confirmation page?"""
        await self.report_nef.query(self.pacer_doc_id_nef)
        data_report = self.report_nef.data
        self.assertEqual(data_report["document_number"], None)
        self.assertEqual(data_report["docket_number"], "3:18-cv-04865-EMC")
        self.assertEqual(data_report["cost"], "0.10")
        self.assertEqual(data_report["billable_pages"], "1")
        self.assertEqual(data_report["document_description"], "Image670-0")

    @SKIP_IF_NO_PACER_LOGIN
    async def test_no_confirmation_page_pdf_returned_district(self):
        """If the district download confirmation page is not available an empty
        dictionary is returned"""
        await self.report_nef_no_confirmation.query(
            self.pacer_doc_id_nef_no_confirmation
        )
        data_report = self.report_nef_no_confirmation.data
        self.assertEqual(data_report, {})
