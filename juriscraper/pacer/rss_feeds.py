import argparse
import os
import pprint
import re
import sys
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

"""
As of 2018-04-25, the jurisdictions below do not have functional RSS feeds. I 
reached out to all of these jurisdictions and heard back the following:
 
 - miwb: Sent email. Left a VM.
 - nceb: "The Judges in our District have given direction that they do not want 
   the RSS feed turned on in our court.  This has been discussed several times 
   and their decision remains the same."
    - Update via email: "At this time, the court declined to participate.  
      However, the court anticipates transitioning to the NextGen version of 
      CM/ECF in 2019 and will likely participate at that time.
 - nmib (Northern Mariana Islands, 17 hours ahead): Sent email.
 - alnd: Sent email.
 - caed: Sent email. 916-930-4000, left message with IT director, Richard.
 - flnd: Sent email.
 - gand: Left a message at the "Systems" department
 - gasd: Sent email.
 - hid: Sent email. 808-541-1304, Lian Abernathy, Chief Deputy 
 - ilsd: Sent email.
 - kyed: Need to call Sharon Drolijk (Operations Manager) at (859) 233-2503.
 - mdd: Spoke with "Attorney Adviser". He asked for a letter, which I sent. He 
   will take it up with the court, though they didn't have any policy that he 
   was aware of. It's going through their "court committee system for 
   consideration." Seems it wasn't done for performance reasons years ago. They
   will take it up again.
 - msnd: Sent email.
 - mtd: Julie Collins, Deputy Clerk in charge of Billings division, called back. 
   She's going to look into it.
 - ndd: Sent email. 701-530-2313, Clerk of Clerk, Rob. On the to do list. 
   Hopefully by end of the year (2018). Nobody ever asked before.
 - nvd: Sent email. Talked to Robert in "Quality Control". He shook me a bit 
   with how difficult he was. He insists I need to send a letter to the chief 
   judge, but that they're not considering this currently.
    - A different tack: Trying the operations manager, Lia at 775-686-5840. 
      She's friendly. Requested a letter for chief judge. Sent.
 - nywd: Sent email.
 - oked: Sent email.
 - oknd: Sent email.
 - pamd: Sent email.
 - scd: "We have forwarded your request on to management staff at the District 
   Court for further consideration." 
 - tnwd: Sent email.
 - txnd: Left me a long voicemail. They're working on it and have it in 
   committee. Expectation is that they may require an en banc meeting of the 
   judges to make a decision, but that the decision should come soon and be 
   positive.
 - vaed: "We are currently looking into this and will possibly have this 
   feature in the near future."

"""


class PacerRssFeed(DocketReport):
    # The entries are HTML entity-coded, and these matches are run AFTER
    # decoding. A typical entry is of the form:
    #   [short_description] (<a href="doc1_url">document_number</a>)
    # Or a literal example (line breaks added):
    #   [Scheduling Order] (<a href="https://ecf.mad.uscourts.gov/doc1/
    #   09518690740?caseid=186403&de_seq_num=98">39</a>)
    # We use three simple matches rather than a complex one with three groups.
    document_number_regex = re.compile(r'">(\d+)</a>')
    doc1_url_regex = re.compile(r'href="(.*/doc1/.*)"')
    short_desc_regex = re.compile(r'\[(.*?)\]')  # Matches 'foo': [ foo ] (

    PATH = 'cgi-bin/rss_outside.pl'

    CACHE_ATTRS = ['data']

    def __init__(self, court_id):
        super(PacerRssFeed, self).__init__(court_id)
        self._clear_caches()
        self._data = None
        self.session = Session()
        self.is_valid = True

        if self.court_id.endswith('b'):
            self.is_bankruptcy = True
        else:
            self.is_bankruptcy = False

    @property
    def url(self):
        if self.court_id == 'ilnb':
            return "https://tdi.ilnb.uscourts.gov/wwwroot/RSS/rss_outside.xml"
        else:
            return "https://ecf.%s.uscourts.gov/%s" % \
                (self.court_id, self.PATH)

    def query(self):
        """Query the RSS feed for a given court ID

        Note that we use requests here, and so we forgo some of the
        useful features that feedparser offers around the Etags and
        Last-Modified headers. This is fine for now because no PACER
        site seems to support these headers, but eventually we'll
        probably want to do better here. The reason we *don't* use
        feedparser already is because it presents a different set of
        APIs and Exceptions that we don't want to monkey with, at
        least, not yet, and especially not yet if PACER itself doesn't
        seem to care.

        For a good summary of this issue, see:
        https://github.com/freelawproject/juriscraper/issues/195#issuecomment-385848344
        """
        logger.info(u"Querying the RSS feed for %s" % self.court_id)
        timeout = (60, 300)
        self.response = self.session.get(self.url, timeout=timeout)

    def parse(self):
        self._clear_caches()
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
        if self._data is not None:
            return self._data

        data_list = []
        for entry in self.feed.entries:
            try:
                data = self.metadata(entry)
                data[u'parties'] = None
                data[u'docket_entries'] = self.docket_entries(entry)
            except AttributeError:
                # Happens when RSS items lack necessary attributes like a URL
                # or published date.
                pass
            else:
                if data[u'docket_entries'] and data['docket_number']:
                    data_list.append(data)

        self._data = data_list
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
        """Parse the RSS item to get back a docket entry-like object.
        Although there is only one, return it as a list.

        We do not return paperless or so-called "minute orders" that
        lack attached documents (such minute orders may have entry
        numbers).
        """
        de = {
            u'date_filed': date(*entry.published_parsed[:3]),
            u'description': u'',
            u'document_number': self._get_value(self.document_number_regex,
                                                entry.summary),
            u'short_description': html_unescape(
                self._get_value(self.short_desc_regex, entry.summary)),
        }

        doc1_url = self._get_value(self.doc1_url_regex, entry.summary)
        if doc1_url:
            de[u'pacer_doc_id'] = get_pacer_doc_id_from_doc1_url(doc1_url)
        else:
            # Some courts, in particular, NYED do not provide doc1 links and
            # instead provide show_case_doc links. Some docket entries don't
            # provide links. In either case, we can't provide pacer_doc_id.
            de[u'pacer_doc_id'] = u''

        if not de[u'document_number']:
            return []

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
        try:
            case_name = title_text.split(' ', 1)[1]
        except IndexError:
            return u"Unknown Case Title"
        case_name = html_unescape(case_name)
        case_name = clean_string(harmonize(case_name))
        return case_name


def _main():
    # For help: python -m juriscraper.pacer.rss_feeds -h
    parser = argparse.ArgumentParser(
        prog="python -m %s.%s" %
        (__package__,
         os.path.splitext(os.path.basename(sys.argv[0]))[0]))
    parser.add_argument('-b', '--bankruptcy', action='store_true',
                        help='Use bankruptcy parser variant.')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('court_or_file', nargs='?', default='-',
                        help='''
A PACER court id or a local filename; defaults to stdin (-).
Any 3 or 4 character string is presumed to be a court;
sorry if that was your filename.''')

    args = parser.parse_args()

    arg_len = len(args.court_or_file)
    if 3 <= arg_len <= 4:
        feed = PacerRssFeed(args.court_or_file)
        print("Querying RSS feed at: %s" % feed.url)
        feed.query()
        print("Parsing RSS feed for %s" % feed.court_id)
        feed.parse()
    else:
        if not args.bankruptcy:
            feed = PacerRssFeed('fake_district_court_id')
        else:
            # final 'b' char is interpretted as bankruptcy
            feed = PacerRssFeed('fake_bankruptcy_court_id_b')
        if args.court_or_file == '-':
            print("Faking up RSS feed from stdin as %s" % feed.court_id)
            f = sys.stdin
        else:
            print("Reading RSS feed from %s as %s" %
                  (args.court_or_file, feed.court_id))
            f = open(args.court_or_file)
        feed._parse_text(f.read().decode('utf-8'))

    print("Got %s items" % len(feed.data))
    if args.verbose:
        print("Here they are:\n")
        pprint.pprint(feed.data, indent=2)


if __name__ == "__main__":
    _main()
