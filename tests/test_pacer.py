# coding=utf-8
from __future__ import print_function

import sys
import time
import unittest
from datetime import timedelta, date

import fnmatch
import jsondate as json
import mock
import os
import vcr
from requests import ConnectionError

from juriscraper.lib.exceptions import PacerLoginException, SlownessException
from juriscraper.lib.html_utils import get_html_parsed_text
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.pacer import DocketReport, FreeOpinionReport
from juriscraper.pacer.http import login, PacerSession
from juriscraper.pacer.utils import (
    get_courts_from_json, get_court_id_from_url,
    get_pacer_case_id_from_docket_url, get_pacer_doc_id_from_doc1_url,
    reverse_goDLS_function, make_doc1_url,
    clean_pacer_object
)
from . import JURISCRAPER_ROOT, TESTS_ROOT

vcr = vcr.VCR(cassette_library_dir=os.path.join(TESTS_ROOT, 'fixtures/cassettes'))

IS_TRAVIS = 'TRAVIS' in os.environ
PACER_USERNAME = os.environ.get('PACER_USERNAME', None)
PACER_PASSWORD = os.environ.get('PACER_PASSWORD', None)
PACER_SETTINGS_MSG = "Skipping test. Please set PACER_USERNAME and " \
                     "PACER_PASSWORD environment variables to run this test."
SKIP_IF_NO_PACER_LOGIN = unittest.skipUnless(
                            (PACER_USERNAME and PACER_PASSWORD),
                            reason=PACER_SETTINGS_MSG)


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

        self.session.post('https://free.law', files=data)

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

        self.session.post('https://free.law', data=data)

        self.assertTrue(mock_post.called,
                        'request.Session.post should be called')
        self.assertNotIn('data', mock_post.call_args[1],
                         'we should intercept data arguments')
        self.assertEqual(expected, mock_post.call_args[1]['files'],
                         'we should transform and populate the files argument')

    @mock.patch('juriscraper.pacer.http.requests.Session.post')
    def test_sets_default_timeout(self, mock_post):
        self.session.post('https://free.law', data={})

        self.assertTrue(mock_post.called,
                        'request.Session.post should be called')
        self.assertIn('timeout', mock_post.call_args[1],
                      'we should add a default timeout automatically')
        self.assertEqual(300, mock_post.call_args[1]['timeout'],
                         'default should be 300')


class PacerAuthTest(unittest.TestCase):
    """Test the authentication methods"""

    @SKIP_IF_NO_PACER_LOGIN
    def test_logging_into_pacer(self):
        court_id = 'ca1'
        try:
            pacer_session = login(court_id, PACER_USERNAME, PACER_PASSWORD)
            self.assertIsNotNone(pacer_session)
            self.assertIsNotNone(pacer_session.cookies.get(
                'PacerSession', None, domain='.uscourts.gov', path='/'))

        except PacerLoginException:
            self.fail('Could not log into court %s' % court_id)

    def test_logging_into_test_site(self):
        try:
            pacer_session = login('psc', 'tr1234', 'Pass!234')
            self.assertIsNotNone(pacer_session)
            self.assertIsNotNone(pacer_session.cookies.get(
                'PacerSession', None, domain='.uscourts.gov', path='/'))

        except PacerLoginException:
            self.fail('Could not log into PACER test site!')


class PacerFreeOpinionsTest(unittest.TestCase):
    """A variety of tests relating to the Free Written Opinions report"""

    @classmethod
    def setUpClass(cls):
        pacer_session = PacerSession()

        if PACER_USERNAME and PACER_PASSWORD:
            # CAND chosen at random
            pacer_session = login('cand', PACER_USERNAME, PACER_PASSWORD)

        with open(os.path.join(JURISCRAPER_ROOT, 'pacer/courts.json')) as j:
            cls.courts = get_courts_from_json(json.load(j))

        with open(os.path.join(TESTS_ROOT, 'fixtures/valid_free_opinion_dates.json')) as j:
            cls.valid_dates = json.load(j)

        cls.reports = {}
        for court in cls.courts:
            court_id = get_court_id_from_url(court['court_link'])
            cls.reports[court_id] = FreeOpinionReport(court_id, pacer_session)

    @unittest.skip('disabling during refactor')
    @vcr.use_cassette(record_mode='new_episodes')
    def test_extract_written_documents_report(self):
        """Do all the written reports work?"""

        for court in self.courts:
            if court['type'] == "U.S. Courts of Appeals":
                continue
            court_id = get_court_id_from_url(court['court_link'])

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
                    raise ValueError("Runaway date query for %s: %s" %
                                     (court_id, some_date))
                try:
                    responses = report.query(some_date, some_date,
                                             sort='case_number')
                except ConnectionError as e:
                    if retry_count <= max_retries:
                        print("%s. Trying again (%s of %s)" %
                              (e, retry_count, max_retries))
                        time.sleep(10)  # Give the server a moment of rest.
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
                        self.assertIsNotNone(v, msg="Value of key %s is None "
                                                    "in court %s" % (k, court_id))

                # Can we download one item from each court?
                r = report.download_pdf(results[0]['pacer_case_id'],
                                        results[0]['pacer_doc_id'])
                if r is None:
                    # Extremely messed up download.
                    continue
                self.assertEqual(r.headers['Content-Type'], 'application/pdf')

    @SKIP_IF_NO_PACER_LOGIN
    @vcr.use_cassette(record_mode='new_episodes')
    def test_download_iframed_report(self):
        """Can we download a PDF document returned in IFrame?"""
        report = self.reports['vib']
        r = report.download_pdf('1507', '1921141093')
        self.assertEqual(r.headers['Content-Type'], 'application/pdf')

    @SKIP_IF_NO_PACER_LOGIN
    def test_download_direct_report(self):
        """Can we download a PDF document returned directly?"""
        report = self.reports['alnb']
        r = report.download_pdf('602431', '018129511556')
        self.assertEqual(r.headers['Content-Type'], 'application/pdf')

    @SKIP_IF_NO_PACER_LOGIN
    def test_query_can_get_multiple_results(self):
        """
        Can we run a query that gets multiple rows and parse them all?
        """
        court_id = 'paeb'
        report = self.reports[court_id]
        some_date = convert_date_string(self.valid_dates[court_id])
        responses = report.query(some_date, some_date, sort='case_number')
        results = report.parse(responses)
        self.assertEqual(3, len(results), 'should get 3 responses for ksb')

    @SKIP_IF_NO_PACER_LOGIN
    def test_query_using_last_good_row(self):
        """
        Can we run a query that triggers no content in first cell?
        """
        court_id = 'ksb'
        report = self.reports[court_id]
        some_date = convert_date_string(self.valid_dates[court_id])
        responses = report.query(some_date, some_date, sort='case_number')
        results = report.parse(responses)
        self.assertEqual(2, len(results), 'should get 2 response for ksb')

    @SKIP_IF_NO_PACER_LOGIN
    def test_ordering_by_date_filed(self):
        """Can we change the ordering?"""
        # First try both orderings in areb (where things have special cases) and
        # ded (Delaware) where things are more normal.
        tests = (
            {'court': 'areb', 'count': 1},
            {'court': 'ded', 'count': 4}
        )
        for test in tests:
            report = self.reports[test['court']]
            some_date = convert_date_string(self.valid_dates[test['court']])
            responses = report.query(some_date, some_date, sort='date_filed')
            results = report.parse(responses)
            self.assertEqual(
                test['count'],
                len(results),
                'Should get %s response for %s' % (test['count'], test['court'])
            )
            responses = report.query(some_date, some_date, sort='case_number')
            results = report.parse(responses)
            self.assertEqual(
                test['count'],
                len(results),
                'should get %s response for %s' % (test['count'], test['court'])
            )

    def test_catch_excluded_court_ids(self):
        """Do we properly catch and prevent a query against disused courts?"""
        mock_session = mock.MagicMock()

        report = self.reports['ganb']
        report.session = mock_session

        some_date = convert_date_string('1/1/2015')

        results = report.query(some_date, some_date, sort='case_number')
        self.assertEqual([], results, 'should have empty result set')
        self.assertFalse(mock_session.post.called, 'should not trigger a POST query')

        report = self.reports['cand']
        report.session = mock_session
        report.query(some_date, some_date, sort='case_number')
        self.assertTrue(mock_session.post.called, 'good court should POST')


class PacerDocketReportTest(unittest.TestCase):
    """A variety of tests for the docket report"""

    @classmethod
    def setUpClass(cls):
        pacer_session = login('psc', 'tr1234', 'Pass!234')
        cls.report = DocketReport('psc', pacer_session)
        cls.pacer_case_id = '62866'

    @staticmethod
    def _count_rows(html):
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
        row_count = self._count_rows(r.text)
        self.assertEqual(row_count, 25, msg="Didn't get expected number of "
                                            "rows when filtering by start "
                                            "date. Got %s." % row_count)

        r = self.report.query(self.pacer_case_id, date_start=date(2007, 2, 7),
                              date_end=date(2007, 2, 8))
        row_count = self._count_rows(r.text)
        self.assertEqual(row_count, 2, msg="Didn't get expected number of "
                                           "rows when filtering by start and "
                                           "end dates. Got %s." % row_count)

        r = self.report.query(self.pacer_case_id, doc_num_start=5,
                              doc_num_end=5)
        row_count = self._count_rows(r.text)
        self.assertEqual(row_count, 1, msg="Didn't get expected number of rows "
                                           "when filtering by doc number. Got "
                                           "%s" % row_count)

        r = self.report.query(self.pacer_case_id, date_start=date(2007, 2, 7),
                              date_end=date(2007, 2, 8), date_range_type="Entered")
        row_count = self._count_rows(r.text)
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


class DocketParseTest(unittest.TestCase):
    """Lots of docket parsing tests."""

    def setUp(self):
        self.maxDiff = 200000

    def run_parsers_on_path(self, path_root):
        """Test all the parsers, faking the network query."""
        paths = []
        for root, dirnames, filenames in os.walk(path_root):
            for filename in fnmatch.filter(filenames, '*.html'):
                paths.append(os.path.join(root, filename))
        paths.sort()
        path_max_len = max(len(path) for path in paths) + 2
        for i, path in enumerate(paths):
            sys.stdout.write("%s. Doing %s" % (i, path.ljust(path_max_len)))
            t1 = time.time()
            dirname, filename = os.path.split(path)
            filename_sans_ext = filename.split('.')[0]
            json_path = os.path.join(dirname, '%s.json' % filename_sans_ext)
            court = filename_sans_ext.split('_')[0]

            report = DocketReport(court)
            with open(path, 'r') as f:
                report.parse_text(f.read().decode('utf-8'))
            data = report.data

            # Make sure some required fields are populated.
            fields = ['date_filed', 'case_name', 'docket_number']
            for field in fields:
                self.assertTrue(
                    data[field],
                    msg="Unable to find truthy value for field %s" % field,
                )

            self.assertEqual(data['court_id'], court)

            # Party-specific tests...
            for party in data['parties']:
                self.assertTrue(
                    party.get('name', False),
                    msg="Every party must have a name attribute. Did not get a "
                        "value for:\n\n%s" % party
                )
                # Protect against effed up adversary proceedings cases that
                # don't parse properly. See: cacb, 2:08-ap-01570-BB
                self.assertNotIn('----', party['name'])

            if not os.path.isfile(json_path):
                bar = "*" * 50
                print("\n\n%s\nJSON FILE DID NOT EXIST. CREATING IT AT:"
                      "\n\n  %s\n\n"
                      "Please test the data in this file before assuming "
                      "everything worked.\n%s\n" % (bar, json_path, bar))
                with open(json_path, 'w') as f:
                    json.dump(data, f, indent=2, sort_keys=True)
                    #self.assertFalse(True)
                    continue

            with open(json_path) as f:
                j = json.load(f)
                # Compare docket entries and parties first, for easier
                # debugging, then compare whole objects to be sure.
                self.assertEqual(j['docket_entries'], data['docket_entries'])
                self.assertEqual(j['parties'], data['parties'])
                self.assertEqual(j, data)
            t2 = time.time()

            max_duration = 1
            duration = t2 - t1
            if duration > max_duration:
                if sys.gettrace() is None and not IS_TRAVIS:
                    # Don't do this if we're debugging.
                    raise SlownessException(
                        "The parser for '{fn}' took {duration}s to test, "
                        "which is more than the maximum allowed duration of "
                        "{max_duration}s.".format(
                            fn=filename,
                            duration=duration,
                            max_duration=max_duration,
                        )
                    )
            sys.stdout.write("✓ - %0.1fs\n" % (t2-t1))

    def test_bankruptcy_court_dockets(self):
        path_root = os.path.join(TESTS_ROOT, "examples", "pacer", "dockets",
                                 "bankruptcy")
        self.run_parsers_on_path(path_root)

    def test_district_court_dockets(self):
        path_root = os.path.join(TESTS_ROOT, 'examples', 'pacer', 'dockets',
                                 'district')
        self.run_parsers_on_path(path_root)

    def test_specialty_court_dockets(self):
        path_root = os.path.join(TESTS_ROOT, 'examples', 'pacer', 'dockets',
                                 'special')
        self.run_parsers_on_path(path_root)


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
            ('https://ecf.akb.uscourts.gov/doc1/02201247000?caseid=7738&de_seq_num=723284&dm_id=1204742&doc_num=8805&pdf_header=0', '02201247000'),
        )
        for q, a in qa_pairs:
            self.assertEqual(get_pacer_doc_id_from_doc1_url(q), a)

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

    def test_clean_pacer_objects(self):
        """Can we properly clean various types of data?"""
        tests = ({
            # Basic string
            'q': 'asdf , asdf',
            'a': 'asdf, asdf'
        }, {
            # Basic list
            'q': ['asdf , asdf', 'sdfg , sdfg'],
            'a': ['asdf, asdf', 'sdfg, sdfg'],
        }, {
            # Basic dict
            'q': {'a': 'asdf , asdf'},
            'a': {'a': 'asdf, asdf'},
        }, {
            # Nested dict in a list with a string
            'q': [{'a': 'asdf , asdf'}, 'asdf , asdf'],
            'a': [{'a': 'asdf, asdf'}, 'asdf, asdf'],
        }, {
            # Multi-deep nest
            'q': {'a': ['asdf, asdf', 'asdf', {'a': 'asdf  , asdf'}]},
            'a': {'a': ['asdf, asdf', 'asdf', {'a': 'asdf, asdf'}]},
        }, {
            # Date object
            'q': [date(2017, 5, 5), 'asdf , asdf'],
            'a': [date(2017, 5, 5), 'asdf, asdf'],
        }, {
            # Stripping and normalizing whitespace junk
            'q': [' asdf , asdf\n  asdf'],
            'a': ['asdf, asdf asdf'],
        })
        for test in tests:
            self.assertEqual(clean_pacer_object(test['q']), test['a'])
