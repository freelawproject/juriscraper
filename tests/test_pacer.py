import json
import unittest

import requests
import vcr
from datetime import timedelta

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.pacer import private_settings
from juriscraper.pacer.auth import login
from juriscraper.pacer.free_documents import (
    get_written_report_token, query_free_documents_report, download_pdf,
    parse_written_opinions_report
)
from juriscraper.pacer.utils import (
    get_courts_from_json, get_court_id_from_url,
    get_pacer_case_id_from_docket_url, get_pacer_document_number_from_doc1_url,
    reverse_goDLS_function, make_doc1_url
)

vcr = vcr.VCR(cassette_library_dir='tests/fixtures/cassettes')


class PacerAuthTest(unittest.TestCase):
    """Test the authentication methods"""

    def setUp(self):
        # Get the latest court info from our Heroku app.
        with open('juriscraper/pacer/courts.json') as j:
            self.courts = get_courts_from_json(json.load(j))
        self.username = private_settings.PACER_USERNAME
        self.password = private_settings.PACER_PASSWORD

    @vcr.use_cassette()
    def test_logging_in(self):
        for court in self.courts:
            court_id = get_court_id_from_url(court['court_link'])
            login(court_id, self.username, self.password)


class PacerFreeOpinionsTest(unittest.TestCase):
    """A variety of tests relating to the Free Written Opinions report"""
    def setUp(self):
        self.username = private_settings.PACER_USERNAME
        self.password = private_settings.PACER_PASSWORD
        # CAND chosen at random
        self.cookie = login('cand', self.username, self.password)
        self.session = requests.session()
        self.session.cookies.set(**self.cookie)
        with open('juriscraper/pacer/courts.json') as j:
            self.courts = get_courts_from_json(json.load(j))

    @vcr.use_cassette(record_mode='new_episodes')
    def test_get_written_report_token(self):
        """Can we extract the CSRF token from every written report?"""
        for court in self.courts:
            if court['type'] == "U.S. Courts of Appeals":
                # No written opinion reports.
                continue
            court_id = get_court_id_from_url(court['court_link'])
            _ = get_written_report_token(court_id, self.session)

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
                some_date = convert_date_string(valid_dates[court_id])
                while not results:
                    # This loop is sometimes needed to find a date with
                    # documents. In general the valid dates json object should
                    # suffice, however.
                    responses = query_free_documents_report(court_id, some_date,
                                                            some_date, self.cookie)
                    if not responses:
                        break  # Not a supported court.
                    results = parse_written_opinions_report(responses)
                    some_date += timedelta(days=1)

                for result in results:
                    for k, v in result.items():
                        if k in ['nature_of_suit', 'cause']:
                            continue
                        self.assertIsNotNone(v, msg="Value of key %s is None "
                                                    "in court %s" % (k, court_id))

                # Can we download one item from each court?
                r = download_pdf(court_id, results[0]['pacer_case_id'],
                                 results[0]['pacer_document_number'],
                                 self.cookie)
                if r is None:
                    # Extremely messed up download.
                    continue
                self.assertEqual(r.headers['Content-Type'], 'application/pdf')

    @vcr.use_cassette(record_mode='new_episodes')
    def test_download_a_free_document(self):
        """Can we download a free document?"""
        r = download_pdf('vib', '1507', '1921141093', self.cookie)
        self.assertEqual(r.headers['Content-Type'], 'application/pdf')


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
