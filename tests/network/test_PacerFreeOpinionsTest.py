#!/usr/bin/env python
# coding=utf-8


import os
import time
import unittest
from datetime import date, timedelta

import jsondate3 as json
from unittest import mock
from requests import ConnectionError

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.pacer import FreeOpinionReport
from juriscraper.pacer.http import PacerSession
from juriscraper.pacer.utils import get_court_id_from_url, get_courts_from_json
from tests import JURISCRAPER_ROOT, TESTS_ROOT_EXAMPLES_PACER
from tests.network import (
    SKIP_IF_NO_PACER_LOGIN,
    get_pacer_session,
    pacer_credentials_are_defined,
)


class PacerFreeOpinionsTest(unittest.TestCase):
    """A variety of tests relating to the Free Written Opinions report"""

    def setUp(self):
        pacer_session = PacerSession()

        if pacer_credentials_are_defined():
            # CAND chosen at random
            pacer_session = get_pacer_session()
            pacer_session.login()

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
    def test_extract_written_documents_report(self):
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
                        "Runaway date query for %s: %s" % (court_id, some_date)
                    )
                try:
                    report.query(some_date, some_date, sort="case_number")
                except ConnectionError as e:
                    if retry_count <= max_retries:
                        print(
                            "%s. Trying again (%s of %s)"
                            % (e, retry_count, max_retries)
                        )
                        time.sleep(10)  # Give the server a moment of rest.
                        retry_count += 1
                        continue
                    else:
                        print("%s: Repeated errors at this court." % e)
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
                r = report.download_pdf(
                    results[0]["pacer_case_id"], results[0]["pacer_doc_id"]
                )
                if r is None:
                    # Extremely messed up download.
                    continue
                self.assertEqual(r.headers["Content-Type"], "application/pdf")

    @SKIP_IF_NO_PACER_LOGIN
    def test_download_simple_pdf(self):
        """Can we download a PDF document returned directly?"""
        report = self.reports["alnb"]
        r = report.download_pdf("602431", "018129511556")
        self.assertEqual(r.headers["Content-Type"], "application/pdf")

    @SKIP_IF_NO_PACER_LOGIN
    def test_download_iframed_pdf(self):
        """Can we download a PDF document returned in IFrame?"""
        report = self.reports["vib"]
        r = report.download_pdf("1507", "1921141093")
        self.assertEqual(r.headers["Content-Type"], "application/pdf")

    @SKIP_IF_NO_PACER_LOGIN
    def test_download_unavailable_pdf(self):
        """Do we throw an error if the item is unavailable?"""
        # 5:11-cr-40057-JAR, document 3
        report = self.reports["ksd"]
        r = report.download_pdf("81531", "07902639735")
        self.assertIsNone(r)

    @SKIP_IF_NO_PACER_LOGIN
    def test_query_can_get_multiple_results(self):
        """
        Can we run a query that gets multiple rows and parse them all?
        """
        court_id = "paeb"
        report = self.reports[court_id]
        some_date = convert_date_string(self.valid_dates[court_id])
        report.query(some_date, some_date, sort="case_number")
        self.assertEqual(3, len(report.data), "should get 3 responses for ksb")

    @SKIP_IF_NO_PACER_LOGIN
    def test_query_using_last_good_row(self):
        """
        Can we run a query that triggers no content in first cell?
        """
        court_id = "ksb"
        report = self.reports[court_id]
        some_date = convert_date_string(self.valid_dates[court_id])
        report.query(some_date, some_date, sort="case_number")
        self.assertEqual(2, len(report.data), "should get 2 response for ksb")

    @SKIP_IF_NO_PACER_LOGIN
    def test_ordering_by_date_filed(self):
        """Can we change the ordering?"""
        # First try both orderings in areb (where things have special cases) and
        # ded (Delaware) where things are more normal.
        tests = ({"court": "areb", "count": 1}, {"court": "ded", "count": 4})
        for test in tests:
            report = self.reports[test["court"]]
            some_date = convert_date_string(self.valid_dates[test["court"]])
            report.query(some_date, some_date, sort="date_filed")
            self.assertEqual(
                test["count"],
                len(report.data),
                "Should get %s response for %s"
                % (test["count"], test["court"]),
            )
            report.query(some_date, some_date, sort="case_number")
            self.assertEqual(
                test["count"],
                len(report.data),
                "should get %s response for %s"
                % (test["count"], test["court"]),
            )

    def test_catch_excluded_court_ids(self):
        """Do we properly catch and prevent a query against disused courts?"""
        mock_session = mock.MagicMock()

        report = self.reports["casb"]
        report.session = mock_session

        some_date = convert_date_string("1/1/2015")

        report.query(some_date, some_date, sort="case_number")
        self.assertEqual([], report.responses, "should have empty result set")
        self.assertFalse(
            mock_session.post.called, msg="should not trigger a POST query"
        )
