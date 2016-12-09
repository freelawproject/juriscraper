import json
import unittest

import requests
import vcr

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.pacer import private_settings
from juriscraper.pacer.auth import login
from juriscraper.pacer.free_documents import (
    get_written_report_token, query_free_documents_report,
    parse_written_opinions_report
)
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
            court_id = get_court_id_from_url(court['court_link'])
            token = get_written_report_token(court_id, self.session)

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
                some_date = convert_date_string(valid_dates[court_id])
                responses = query_free_documents_report(court_id, some_date,
                                                        some_date, self.cookie)
                if not responses:
                    break  # Not a supported court.
                results = parse_written_opinions_report(responses)
            else:
                print "No valid date found for %s" % court_id
