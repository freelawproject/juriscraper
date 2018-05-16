import pprint
import sys

from lxml.html import HtmlElement

from .docket_report import BaseDocketReport
from .reports import BaseReport
from .utils import clean_pacer_object
from ..lib.string_utils import clean_string, convert_date_string
from ..lib.utils import previous_and_next


# Patch the HtmlElement class to add a function that can handle regular
# expressions within XPath queries. See usages throughout AppellateDocketReport.
def re_xpath(self, path):
    return self.xpath(path, namespaces={
        're': 'http://exslt.org/regular-expressions'})
HtmlElement.re_xpath = re_xpath


class AppellateDocketReport(BaseDocketReport, BaseReport):
    PATH = 'xxx'  # xxx for self.query
    CACHE_ATTRS = ['metadata', 'parties', 'docket_entries']

    def query(self, *args, **kwargs):
        raise NotImplementedError("We currently do not support querying "
                                  "appellate docket reports.")

    def __init__(self, court_id, pacer_session=None):
        super(AppellateDocketReport, self).__init__(court_id, pacer_session)
        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata = None
        self._parties = None
        self._docket_entries = None

    def download_pdf(self, pacer_case_id, pacer_document_number):
        # xxx this is likely to need to be overridden.
        pass

    @property
    def metadata(self):
        if self._metadata is not None:
            return self._metadata

        data = {
            u'court_id': self.court_id,
            u'docket_number': self._get_tail_by_regex("Docket #"),
            # u'case_name': '',
            u'date_converted': None,
            u'date_discharged': None,
            # u'assigned_to_str': self._get_judge(self.assigned_to_regex),
            # u'referred_to_str': self._get_judge(self.referred_to_regex),
            # u'cause': self._get_value(self.cause_regex, self.metadata_values),
            u'nature_of_suit': self._get_tail_by_regex("Nature of Suit"),
            # u'jury_demand': self._get_value(self.jury_demand_regex,
            #                                 self.metadata_values),
            # u'demand': self._get_value(self.demand_regex,
            #                            self.metadata_values),
            # u'jurisdiction': self._get_value(self.jurisdiction_regex,
            #                                  self.metadata_values),
            u'appeal_from': self._get_tail_by_regex('Appeal From'),
            u'fee_status': self._get_tail_by_regex('Fee Status'),
            u'date_filed': self._get_tail_by_regex('Docketed', True),
            u'date_terminated': self._get_tail_by_regex('Termed', True),
        }
        data = clean_pacer_object(data)
        self._metadata = data
        return data

    @property
    def parties(self):
        """Get the party info from the HTML or return it if it's cached.

        The data here will look like this:

            parties = [{
                'name': 'NATIONAL VETERANS LEGAL SERVICES PROGRAM',
                'type': 'Plaintiff',
                'date_terminated': '2018-03-12',
                'extra_info': ("1600 K Street, NW\n"
                               "Washington, DC 20006"),
                'attorneys': [{
                    'name': 'William H. Narwold',
                    'contact': ("1 Corporate Center\n",
                                "20 Church Street\n",
                                "17th Floor\n",
                                "Hartford, CT 06103\n",
                                "860-882-1676\n",
                                "Fax: 860-882-1682\n",
                                "Email: bnarwold@motleyrice.com"),
                    'roles': ['LEAD ATTORNEY',
                              'PRO HAC VICE',
                              'ATTORNEY TO BE NOTICED'],
                }, {
                    ...more attorneys here...
                }]
            }, {
                ...more parties (and their attorneys) here...
            }]
        """
        if self._parties is not None:
            return self._parties

        path = 'xxx'
        party_rows = self.tree.xpath(path)

        parties = []
        party = {}
        for prev, row, nxt in previous_and_next(party_rows):
            # xxx get party metadata here
            cells = row.xpath('xxx')
            if len(cells) == 3 and party != {}:
                party[u'attorneys'] = self._get_attorneys(cells[2])

            if party not in parties and party != {}:
                # Sometimes there are dups in the docket. Avoid them.
                parties.append(party)

        parties = self._normalize_see_above_attorneys(parties)
        self._parties = parties
        return parties

    def _get_attorneys(self, cell):
        # Get the attorneys here.
        pass

    @property
    def docket_entries(self):
        """Get the docket entries"""
        if self._docket_entries is not None:
            return self._docket_entries

        docket_entry_rows = self.tree.xpath(
            'xxx'
        )[1:]  # Skip the first row
        docket_entries = []
        for row in docket_entry_rows:
            de = {}

        docket_entries = clean_pacer_object(docket_entries)
        self._docket_entries = docket_entries
        return docket_entries

    def _get_tail_by_regex(self, regex, cast_to_date=False):
        """Search all text nodes for a string that matches the regex, then
        return the `tail`ing text.

        :param regex: A regex to search for in all text nodes.
        :param cast_to_date: Whether to convert the resulting text to a date.
        :returns unicode object: The tailing string cleaned up and optionally
        converted to a date.
        """
        tail = clean_string(self.tree.re_xpath(
            '//*[re:match(text(), "%s")]' % regex
        )[0].tail.strip())
        if cast_to_date:
            return convert_date_string(tail)
        return tail


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.appellate_docket filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)
    report = AppellateDocketReport(
        'ca9')  # Court ID is only needed for querying.
    filepath = sys.argv[1]
    print("Parsing HTML file at %s" % filepath)
    with open(filepath, 'r') as f:
        text = f.read().decode('utf-8')
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)
