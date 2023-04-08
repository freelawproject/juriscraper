import argparse
import os
import pprint
import re
import sys
from html import unescape

import feedparser
from requests import Session

from ..lib.log_tools import make_default_logger
from ..lib.string_utils import clean_string, harmonize
from ..lib.utils import clean_court_object
from .docket_report import DocketReport
from .utils import (
    get_pacer_case_id_from_nonce_url,
    get_pacer_doc_id_from_doc1_url,
    get_pacer_seq_no_from_doc1_url,
    parse_datetime_for_us_timezone,
    set_pacer_doc_id_as_appellate_document_number,
)

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


def append_or_merge_entry(docket_list, new_docket):
    """Append new entry to our output or merge it if it's a multi-event entry.

    CMECF entries can contain multiple events, e.g. anyone filing a Motion can
    select one or more of the event types; so too for judicial orders. When
    this is rendered in the RSS feed, it is rendered as two (or more) entries
    for the same case document, with identical times, titles, links, and guids.

    If the new entry is part of a multi-event entry, merge it with the prior
    one. If it's not, append it to the list.

    :param docket_list: A list of docket-like dictionaries, each containing
    docket entries
    :param new_docket: A new docket-like dictionary that can be appended or
    merged into the docket_list.
    :return None
    """
    for docket in docket_list:
        entry = docket["docket_entries"][0]
        new_entry = new_docket["docket_entries"][0]
        same_dn = docket["docket_number"] == new_docket["docket_number"]
        same_cn = docket["pacer_case_id"] == new_docket["pacer_case_id"]
        same_date = entry["date_filed"] == new_entry["date_filed"]
        same_doc_id = entry["pacer_doc_id"] == new_entry["pacer_doc_id"]
        if all([same_dn, same_cn, same_date, same_doc_id]):
            # if docket number, pacer_case_id, date filing, and pacer_doc_id
            # are same, order short descriptions alphabetically and merge.

            short_descriptions = [
                desc.strip()
                for desc in entry["short_description"].split("AND")
            ]
            short_descriptions.append(new_entry["short_description"])
            short_description = " AND ".join(sorted(short_descriptions))
            entry["short_description"] = short_description
            break
    else:
        # Loop exited without hitting a break; item is distinct; append.
        docket_list.append(new_docket)


class PacerRssFeed(DocketReport):
    # The entries are HTML entity-coded, and these matches are run AFTER
    # decoding. A typical entry is of the form:
    #   [short_description] (<a href="doc1_url">document_number</a>)
    # Or a literal example (line breaks added):
    #   [Scheduling Order] (<a href="https://ecf.mad.uscourts.gov/doc1/
    #   09518690740?caseid=186403&de_seq_num=98">39</a>)
    # We use three simple matches rather than a complex one with three groups.
    document_number_regex = re.compile(r"[\"|\'] ?>(\d+)</a>")
    doc1_url_regex = re.compile(r"href=[\"|\'](.*/doc1/.*)[\"|\']")
    docs1_url_regex = re.compile(r"href=[\"|\'](.*/docs1/.*)[\"|\']")
    short_desc_regex = re.compile(r"\[(.*?)\]")  # Matches 'foo': [ foo ] (

    PATH = "cgi-bin/rss_outside.pl"

    CACHE_ATTRS = ["data"]

    def __init__(self, court_id):
        super().__init__(court_id)
        self._clear_caches()
        self._data = None
        self.session = Session()
        self.is_valid = True
        self.is_appellate = False
        if self.court_id[-1].isdigit() or self.court_id in [
            "cadc",
            "cafc",
            "cavc",
        ]:
            self.is_appellate = True
        if self.court_id.endswith("b"):
            self.is_bankruptcy = True
        else:
            self.is_bankruptcy = False

    def __del__(self):
        if self.session:
            self.session.close()

    @property
    def url(self):
        if self.court_id == "nyed":
            # EDNY has some special RSS software. In Sept. 2017,
            # rss_outside.pl redirected to readyDockets.pl:
            #   https://twitter.com/johnhawkinson/status/906005915622629376
            # But that had stopped happening by 2020.
            # Special case it for now, but EDNY/AOUSC follow is required:
            return "https://ecf.nyed.uscourts.gov/cgi-bin/readyDockets.pl"
        elif self.court_id == "ared":
            # In response to requests from their bar association, the Eastern
            # District of Arkansas has a bunch of RSS feeds that you can see
            # from their homepage. Their default one is limited to orders and
            # opinions, but this one has "All Docket Entries".
            return "https://ecf.ared.uscourts.gov/cgi-bin/rss_outside4.pl"
        elif self.is_appellate:
            return f"https://ecf.{self.court_id}.uscourts.gov/n/beam/servlet/TransportRoom?servlet=RSSGenerator"
        else:
            return f"https://ecf.{self.court_id}.uscourts.gov/{self.PATH}"

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
        logger.info(f"Querying the RSS feed for {self.court_id}")
        # The timeout here is a bit tricky. Too long, and national PACER
        # outages cause us grief. Too short and slow courts don't get done.
        # Previously, this value has been (60, 300), then 5. Hopefully the
        # below is a reasonable middle ground.
        timeout = (5, 20)
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

        docket_list = []
        for entry in self.feed.entries:
            try:
                new_docket = self.metadata(entry)
                new_docket["parties"] = None
                new_docket["docket_entries"] = self.docket_entries(entry)
            except AttributeError:
                # Happens when RSS items lack necessary attributes like a URL
                # or published date.
                pass
            else:
                if (
                    new_docket["docket_entries"]
                    and new_docket["docket_number"]
                ):
                    append_or_merge_entry(docket_list, new_docket)

        self._data = docket_list
        return docket_list

    def metadata(self, entry):
        if self.is_valid is False:
            return {}

        data = {
            "court_id": self.court_id,
            "pacer_case_id": get_pacer_case_id_from_nonce_url(entry.link)
            if not self.is_appellate
            else None,
            "docket_number": self._get_docket_number(entry.title),
            "case_name": self._get_case_name(entry.title),
            # Filing date is not available. Also the case for free opinions.
            "date_filed": None,
            "date_terminated": None,
            "date_converted": None,
            "date_discharged": None,
            "assigned_to_str": "",
            "referred_to_str": "",
            "cause": "",
            "nature_of_suit": "",
            "jury_demand": "",
            "demand": "",
            "jurisdiction": "",
            # bankruptcy data
            "trustee_str": "",
            "type": "",
            "office": "",
            "chapter": "",
        }
        data.update(self._parse_get_trustee_type_office_chapter(entry.summary))
        data = clean_court_object(data)
        return data

    @property
    def parties(self):
        raise NotImplementedError("No parties for RSS feeds.")

    def docket_entries(self, entry):
        """Parse the RSS item to get back a docket entry-like object.
        Although there is only one, return it as a list.
        """
        de = {
            "date_filed": parse_datetime_for_us_timezone(entry.published),
            "description": "",
            "document_number": self._get_value(
                self.document_number_regex, entry.summary
            )
            or None,
            "short_description": unescape(
                self._get_value(self.short_desc_regex, entry.summary)
            ),
        }

        # District and bankruptcy doc URL
        doc1_url = self._get_value(self.doc1_url_regex, entry.summary)
        # Appellate doc URL
        docs1_url = self._get_value(self.docs1_url_regex, entry.summary)
        if doc1_url:
            de["pacer_doc_id"] = get_pacer_doc_id_from_doc1_url(doc1_url)
            de["pacer_seq_no"] = get_pacer_seq_no_from_doc1_url(doc1_url)
        elif docs1_url:
            de["pacer_doc_id"] = get_pacer_doc_id_from_doc1_url(docs1_url)
            de["pacer_seq_no"] = None
        else:
            # Some courts, in particular, NYED do not provide doc1 links and
            # instead provide show_case_doc links. Some docket entries don't
            # provide links. In either case, we can't provide pacer_doc_id.
            de["pacer_doc_id"] = ""
            de["pacer_seq_no"] = None

        if self.is_appellate:
            set_pacer_doc_id_as_appellate_document_number(de)

        return [de]

    def _parse_get_trustee_type_office_chapter(self, entry_text):
        if not self.is_bankruptcy:
            return {}
        data_parts_re = re.compile(
            r"""
            ^Type: (?P<type>.*?)
            Office: (?P<office>.*?)
            Chapter: (?P<chapter>.*?)
            (Trustee: (?P<trustee>.*?))? \[""",
            re.VERBOSE,
        )
        m = data_parts_re.search(entry_text)
        return {
            "type": m.group("type"),
            "office": m.group("office"),
            "chapter": m.group("chapter"),
            "trustee_str": m.group("trustee") or "",
        }

    def _get_docket_number(self, title_text):
        if self.is_bankruptcy:
            # Uses both b/c sometimes the bankr. cases have a dist-style docket
            # number.
            regexes = [
                self.docket_number_dist_regex,
                self.docket_number_bankr_regex,
            ]
        elif self.is_appellate:
            regexes = [self.docket_number_appellate_regex]
        else:
            regexes = [self.docket_number_dist_regex]
        for regex in regexes:
            match = regex.search(title_text)
            if match:
                return match.group(1)

    def _get_case_name(self, title_text):
        # 1:18-cv-04423 Chau v. Gorg &amp; Smith et al --> Chau v. Gorg & Smith
        try:
            case_name = title_text.split(" ", 1)[1]
        except IndexError:
            return "Unknown Case Title"
        case_name = unescape(case_name)
        case_name = clean_string(harmonize(case_name))
        return case_name


def _main():
    # For help: python -m juriscraper.pacer.rss_feeds -h
    parser = argparse.ArgumentParser(
        prog="python -m %s.%s"
        % (__package__, os.path.splitext(os.path.basename(sys.argv[0]))[0])
    )
    parser.add_argument(
        "-b",
        "--bankruptcy",
        action="store_true",
        help="Use bankruptcy parser variant.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "court_or_file",
        nargs="?",
        default="-",
        help="""
A PACER court id or a local filename; defaults to stdin (-).
Any 3 or 4 character string is presumed to be a court;
sorry if that was your filename.""",
    )

    args = parser.parse_args()

    arg_len = len(args.court_or_file)
    if 3 <= arg_len <= 4:
        feed = PacerRssFeed(args.court_or_file)
        print(f"Querying RSS feed at: {feed.url}")
        feed.query()
        print(f"Parsing RSS feed for {feed.court_id}")
        feed.parse()
    else:
        if not args.bankruptcy:
            feed = PacerRssFeed("fake_district_court_id")
        else:
            # final 'b' char is interpretted as bankruptcy
            feed = PacerRssFeed("fake_bankruptcy_court_id_b")
        if args.court_or_file == "-":
            print(f"Faking up RSS feed from stdin as {feed.court_id}")
            f = sys.stdin
        else:
            print(
                "Reading RSS feed from %s as %s"
                % (args.court_or_file, feed.court_id)
            )
            f = open(args.court_or_file)
        feed._parse_text(f.read().decode("utf-8"))

    print(f"Got {len(feed.data)} items")
    if args.verbose:
        print("Here they are:\n")
        pprint.pprint(feed.data, indent=2)


if __name__ == "__main__":
    _main()
