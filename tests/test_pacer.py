import json
import unittest
from datetime import date

import os
import requests
import sys
import vcr

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from juriscraper.pacer import private_settings
from juriscraper.pacer.auth import login
from juriscraper.pacer.free_documents import get_written_report_token, \
    query_free_documents_report
from juriscraper.pacer.utils import get_courts_from_json, get_court_id_from_url

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


class PacerParseTest(unittest.TestCase):
    """A variety of tests relating to parsing."""
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
            court_id = get_court_id_from_url(court['court_link'])
            token = get_written_report_token(court_id, self.session)

    @vcr.use_cassette(record_mode='new_episodes')
    def test_extract_written_documents_report(self):
        """Do all the written reports work?"""
        for court in self.courts:
            if court['type'] == "U.S. Courts of Appeals":
                continue
            court_id = get_court_id_from_url(court['court_link'])
            random_day = date(2015, 1, 23)
            query_free_documents_report(court_id, random_day, random_day,
                                        self.cookie)
