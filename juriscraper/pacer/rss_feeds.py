import re
from datetime import date

import feedparser
from requests import Session

from .docket_report import DocketReport
from .utils import clean_pacer_object, get_pacer_case_id_from_docket_url, \
    get_pacer_doc_id_from_doc1_url
from ..lib.html_utils import html_unescape
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import harmonize, clean_string

logger = make_default_logger()


class PacerRssFeed(DocketReport):
    document_number_regex = re.compile(r'">(\d+)</a>')
    doc1_url_regex = re.compile(r'href="(.*)"')
    short_desc_regex = re.compile(r'\[(.*?)\] \(')  # Matches 'foo': [ foo ] (

    PATH = 'cgi-bin/rss_outside.pl'

    def __init__(self, court_id):
        super(PacerRssFeed, self).__init__(court_id)
        self.session = Session()
        self.is_valid = True

        if self.court_id.endswith('b'):
            self.is_bankruptcy = True
        else:
            self.is_bankruptcy = False

    def query(self, court_id):
        """Query the RSS feed for a given court ID"""
        logger.info(u"Querying the RSS feed for %s" % self.court_id)
        self.response = self.session.get(self.url)

    def parse(self):
        self.response.raise_for_status()
        self._parse_text(self.response.text)

    def _parse_text(self, text):
        """Parse the feed and set self.feed

        :param text: The text of the RSS feed.
        :return None
        """
        self.feed = feedparser.parse(text)

    @property
    def data(self):
        """Override this to create a list of docket-like objects instead of the
         usual dict that is usually provided by the docket report.
        """
        data_list = []
        for entry in self.feed.entries:
            data = self.metadata(entry)
            data[u'parties'] = None
            data[u'docket_entries'] = self.docket_entries(entry)
            if data[u'docket_entries']:
                data_list.append(data)
        return data_list

    def metadata(self, entry):
        data = {
            u'court_id': self.court_id,
            u'pacer_case_id': get_pacer_case_id_from_docket_url(entry.link),
            u'docket_number': self._get_docket_number(entry.title),
            u'case_name': self._get_case_name(entry.title),
            # Filing date is not available. Also the case for free opinions.
            u'date_filed': None,
            u'date_terminated': None,
            u'date_converted': None,
            u'date_discharged': None,
            u'assigned_to_str': '',
            u'referred_to_str': '',
            u'cause': '',
            u'nature_of_suit': '',
            u'jury_demand': '',
            u'demand': '',
            u'jurisdiction': '',
        }
        data = clean_pacer_object(data)
        return data

    @property
    def parties(self):
        raise NotImplementedError("No parties for RSS feeds.")

    def docket_entries(self, entry):
        """Parse the RSS item to get back a docket entry-like object"""
        de = {
            u'date_filed': date(*entry.published_parsed[:3]),
            u'document_number': self._get_value(self.document_number_regex,
                                                entry.summary),
            u'description': '',
            u'short_description': html_unescape(
                self._get_value(self.short_desc_regex, entry.summary)),
        }
        doc1_url = self._get_value(self.doc1_url_regex, entry.summary)
        if not all([doc1_url.strip(), de['document_number']]):
            return []

        de[u'pacer_doc_id'] = get_pacer_doc_id_from_doc1_url(doc1_url)

        return [de]

    def _get_docket_number(self, title_text):
        if self.is_bankruptcy:
            # Uses both b/c sometimes the bankr. cases have a dist-style docket
            # number.
            regexes = [self.docket_number_dist_regex,
                       self.docket_number_bankr_regex]
        else:
            regexes = [self.docket_number_dist_regex]
        for regex in regexes:
            match = regex.search(title_text)
            if match:
                return match.group(1)

    def _get_case_name(self, title_text):
        # 1:18-cv-04423 Chau v. Gorg &amp; Smith et al --> Chau v. Gorg & Smith
        case_name = title_text.split(' ', 1)[1]
        case_name = html_unescape(case_name)
        case_name = clean_string(harmonize(case_name))
        return case_name
