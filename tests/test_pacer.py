import json
import os
import time
import unittest
import six
from datetime import timedelta, date

import vcr
import mock
from requests import ConnectionError

from juriscraper.lib.html_utils import get_html_parsed_text
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.pacer import DocketReport, FreeOpinionReport
from juriscraper.pacer.http import login, PacerSession, BadLoginException
from juriscraper.pacer.utils import (
    get_courts_from_json, get_court_id_from_url,
    get_pacer_case_id_from_docket_url, get_pacer_document_number_from_doc1_url,
    reverse_goDLS_function, make_doc1_url
)

vcr = vcr.VCR(cassette_library_dir='tests/fixtures/cassettes')


def get_pacer_credentials_or_skip():
    try:
        username = os.environ['PACER_USERNAME']
        password = os.environ['PACER_PASSWORD']
    except KeyError:
        msg = ("Unable to run PACER tests. Please set PACER_USERNAME and "
               "PACER_PASSWORD environment variables.")
        raise unittest.SkipTest(msg)
    else:
        return username, password


class PacerSessionTest(unittest.TestCase):
    """
    Test the PacerSession wrapper class
    """

    def setUp(self):
        self.session = PacerSession()

    def test_data_transformation(self):
        """
        Test our data transformation routine for building out PACER-compliant
        multi-part form data
        """
        data = {'case_id': 123, 'case_type': 'something'}
        expected = {'case_id': (None, 123), 'case_type': (None, 'something')}
        output = self.session._prepare_multipart_form_data(data)
        self.assertEqual(output, expected)

    @mock.patch('juriscraper.pacer.http.requests.Session.post')
    def test_ignores_non_data_posts(self, mock_post):
        """
        Test that POSTs without a data parameter just pass through as normal.

        :param mock_post: mocked Session.post method
        """
        data = {'name': ('filename', 'junk')}

        self.session.post('http://free.law', files=data)

        self.assertTrue(mock_post.called,
                        'request.Session.post should be called')
        self.assertEqual(data, mock_post.call_args[1]['files'],
                         'the data should not be changed if using a files call')

    @mock.patch('juriscraper.pacer.http.requests.Session.post')
    def test_transforms_data_on_post(self, mock_post):
        """
        Test that POSTs using the data parameter get transformed into PACER's
        delightfully odd multi-part form data.

        :param mock_post: mocked Session.post method
        """
        data = {'name': 'dave', 'age': 33}
        expected = {'name': (None, 'dave'), 'age': (None, 33)}

        self.session.post('http://free.law', data=data)

        self.assertTrue(mock_post.called,
                        'request.Session.post should be called')
        self.assertNotIn('data', mock_post.call_args[1],
                         'we should intercept data arguments')
        self.assertEqual(expected, mock_post.call_args[1]['files'],
                         'we should transform and populate the files argument')

    @mock.patch('juriscraper.pacer.http.requests.Session.post')
    def test_sets_default_timeout(self, mock_post):
        self.session.post('http://free.law', data={})

        self.assertTrue(mock_post.called,
                        'request.Session.post should be called')
        self.assertIn('timeout', mock_post.call_args[1],
                      'we should add a default timeout automatically')
        self.assertEqual(300, mock_post.call_args[1]['timeout'],
                         'default should be 300')


class PacerAuthTest(unittest.TestCase):
    """Test the authentication methods"""

    def setUp(self):
        # Get the latest court info from our Heroku app.
        with open('juriscraper/pacer/courts.json') as j:
            self.courts = get_courts_from_json(json.load(j))
        self.username, self.password = get_pacer_credentials_or_skip()

    @vcr.use_cassette()
    def test_logging_in(self):
        for court in self.courts:
            court_id = get_court_id_from_url(court['court_link'])
            try:
                login(court_id, self.username, self.password)
            except BadLoginException:
                self.fail('Could not log into court %s' % court)


class PacerFreeOpinionsTest(unittest.TestCase):
    """A variety of tests relating to the Free Written Opinions report"""

    def setUp(self):
        self.username, self.password = get_pacer_credentials_or_skip()
        # CAND chosen at random
        cookie_jar = login('cand', self.username, self.password)
        with open('juriscraper/pacer/courts.json') as j:
            self.courts = get_courts_from_json(json.load(j))
        self.reports = {}
        for court in self.courts:
            court_id = get_court_id_from_url(court['court_link'])
            self.reports[court_id] = FreeOpinionReport(court_id, cookie_jar)

    @vcr.use_cassette(record_mode='new_episodes')
    def test_extract_written_documents_report(self):
        """Do all the written reports work?"""
        with open('tests/fixtures/valid_free_opinion_dates.json') as j:
            valid_dates = json.load(j)
        for court in self.courts:
            if court['type'] == "U.S. Courts of Appeals":
                continue
            court_id = get_court_id_from_url(court['court_link'])

            if court_id in valid_dates:
                results = []
                report = self.reports[court_id]
                some_date = convert_date_string(valid_dates[court_id])
                retry_count = 1
                max_retries = 5  # We'll try five times total
                while not results and retry_count <= max_retries:
                    # This loop is sometimes needed to find a date with
                    # documents. In general the valid dates json object should
                    # suffice, however.
                    if some_date > date.today():
                        raise ValueError("Runaway date query for %s: %s" %
                                         (court_id, some_date))
                    try:
                        responses = report.query(some_date, some_date)
                    except ConnectionError as e:
                        if retry_count <= max_retries:
                            print("%s. Trying again (%s of %s)" %
                                (e, retry_count, max_retries))
                            time.sleep(15)  # Give the server a moment of rest.
                            retry_count += 1
                            continue
                        else:
                            print("%s: Repeated errors at this court." % e)
                            raise e
                    if not responses:
                        break  # Not a supported court.
                    results = report.parse(responses)
                    some_date += timedelta(days=1)

                else:
                    # While loop ended normally (without hitting break)
                    for result in results:
                        for k, v in result.items():
                            if k in ['nature_of_suit', 'cause']:
                                continue
                            self.assertIsNotNone(
                                v, msg="Value of key %s is None in court %s" %
                                       (k, court_id)
                            )

                    # Can we download one item from each court?
                    r = report.download_pdf(results[0]['pacer_case_id'],
                                            results[0]['pacer_document_number'])
                    if r is None:
                        # Extremely messed up download.
                        continue
                    self.assertEqual(r.headers['Content-Type'],
                                     'application/pdf')

    @vcr.use_cassette(record_mode='new_episodes')
    def test_download_a_free_document(self):
        """Can we download a free document?"""
        report = self.reports['vib']
        r = report.download_pdf('1507', '1921141093')
        self.assertEqual(r.headers['Content-Type'], 'application/pdf')


class PacerDocketReportTest(unittest.TestCase):
    """A variety of tests for the docket report"""

    def setUp(self):
        cookie = login('psc', 'tr1234', 'Pass!234')
        self.report = DocketReport('psc', cookie)
        self.pacer_case_id = '62866'

    def count_rows(self, html):
        """Count the rows in the docket report.

        :param html: The HTML of the docket report.
        :return: The count of the number of rows.
        """
        tree = get_html_parsed_text(html)
        return len(tree.xpath('//table[./tr/td[3]]/tr')) - 1  # No header row

    @vcr.use_cassette(record_mode='new_episodes')
    def test_queries(self):
        """Do a variety of queries work?"""
        r = self.report.query(self.pacer_case_id)
        self.assertIn('Deft previously', r.text,
                      msg="Super basic query failed")

        r = self.report.query(self.pacer_case_id, date_start=date(2007, 2, 7))
        row_count = self.count_rows(r.text)
        self.assertEqual(row_count, 25, msg="Didn't get expected number of "
                                            "rows when filtering by start "
                                            "date. Got %s." % row_count)

        r = self.report.query(self.pacer_case_id, date_start=date(2007, 2, 7),
                              date_end=date(2007, 2, 8))
        row_count = self.count_rows(r.text)
        self.assertEqual(row_count, 2, msg="Didn't get expected number of "
                                           "rows when filtering by start and "
                                           "end dates. Got %s." % row_count)

        r = self.report.query(self.pacer_case_id, doc_num_start=5,
                              doc_num_end=5)
        row_count = self.count_rows(r.text)
        self.assertEqual(row_count, 1, msg="Didn't get expected number of rows "
                                           "when filtering by doc number. Got "
                                           "%s" % row_count)

        r = self.report.query(self.pacer_case_id, date_start=date(2007, 2, 7),
                              date_end=date(2007, 2, 8), date_range_type="Entered")
        row_count = self.count_rows(r.text)
        self.assertEqual(row_count, 2, msg="Didn't get expected number of rows "
                                           "when filtering by start and end "
                                           "dates and date_range_type of "
                                           "Entered. Got %s" % row_count)

        r = self.report.query(self.pacer_case_id, doc_num_start=500,
                              show_parties_and_counsel=True)
        self.assertIn('deRosas', r.text, msg="Didn't find party info when it "
                                             "was explicitly requested.")
        r = self.report.query(self.pacer_case_id, doc_num_start=500,
                              show_parties_and_counsel=False)
        self.assertNotIn('deRosas', r.text, msg="Got party info but it was not "
                                                "requested.")

        r = self.report.query(self.pacer_case_id, doc_num_start=500,
                              show_terminated_parties=True,
                              show_parties_and_counsel=True)
        self.assertIn('Rosado', r.text, msg="Didn't get terminated party info "
                                            "when it was requested.")
        r = self.report.query(self.pacer_case_id, doc_num_start=500,
                              show_terminated_parties=False)
        self.assertNotIn('Rosado', r.text, msg="Got terminated party info but "
                                               "it wasn't requested.")


class PacerUtilTest(unittest.TestCase):
    """A variety of tests of our simple utilities."""

    def test_getting_case_id_from_urls(self):
        qa_pairs = (
            ('https://ecf.almd.uscourts.gov/cgi-bin/DktRpt.pl?56120',
             '56120'),
            ('https://ecf.azb.uscourts.gov/cgi-bin/iquery.pl?625371913403797-L_9999_1-0-663150',
             '663150')
        )
        for q, a in qa_pairs:
            self.assertEqual(get_pacer_case_id_from_docket_url(q), a)

    def test_getting_court_id_from_url(self):
        qa_pairs = (
            ('https://ecf.almd.uscourts.gov/cgi-bin/DktRpt.pl?56120', 'almd'),
        )
        for q, a in qa_pairs:
            self.assertEqual(get_court_id_from_url(q), a)

    def test_get_pacer_document_number_from_doc1_url(self):
        qa_pairs = (
            ('https://ecf.almd.uscourts.gov/doc1/01712427473', '01712427473'),
            ('/doc1/01712427473', '01712427473'),
        )
        for q, a in qa_pairs:
            self.assertEqual(get_pacer_document_number_from_doc1_url(q), a)

    def test_reverse_dls_function(self):
        """Can we parse the javascript correctly to get a good dict?"""
        qa_pairs = (
            ("goDLS('/doc1/01712427473','56121','69','','','1','','');return(false);",
             {'form_post_url': '/doc1/01712427473', 'caseid': '56121',
              'de_seq_num': '69', 'got_receipt': '', 'pdf_header': '',
              'pdf_toggle_possible': '1', 'magic_num': '', 'hdr': ''}),
        )
        for q, a in qa_pairs:
            self.assertEqual(reverse_goDLS_function(q), a)

    def test_make_doc1_url(self):
        """Can we make good doc1 urls?"""
        qa_pairs = (
            (('cand', '01712427473', False),
             'https://ecf.cand.uscourts.gov/doc1/01712427473'),
            (('cand', '01702427473', False),
             'https://ecf.cand.uscourts.gov/doc1/01702427473'),
            (('cand', '01712427473', True),
             'https://ecf.cand.uscourts.gov/doc1/01712427473'),
            (('cand', '01702427473', True),
             'https://ecf.cand.uscourts.gov/doc1/01712427473'),
        )
        for q, a in qa_pairs:
            self.assertEqual(make_doc1_url(*q), a)
