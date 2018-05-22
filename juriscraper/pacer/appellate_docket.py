import pprint
import re
import sys

from lxml.html import tostring

from .docket_report import BaseDocketReport
from .reports import BaseReport
from .utils import clean_pacer_object, get_court_id_from_url, \
    get_pacer_doc_id_from_doc1_url
from ..lib.judge_parsers import normalize_judge_string
from ..lib.string_utils import clean_string, convert_date_string, harmonize, \
    force_unicode


class AppellateDocketReport(BaseDocketReport, BaseReport):
    """Parse appellate dockets.

    These can be particularly detailed and for the most part we parse the data
    and provide it in our output. There are some exceptions:

     1. We don't parse the Prior/Current Cases table.
     1. We cheat on the parties attribute and just return HTML rather than
        structured data.
     1. We don't handle bankruptcy appellate panel dockets (yet)

    """

    docket_number_dist_regex = re.compile(
        r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})")

    PATH = 'xxx'  # xxx for self.query
    CACHE_ATTRS = ['metadata', 'docket_entries']

    def __init__(self, court_id, pacer_session=None):
        super(AppellateDocketReport, self).__init__(court_id, pacer_session)
        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata = None
        self._parties = None
        self._docket_entries = None

    def query(self, *args, **kwargs):
        raise NotImplementedError("We currently do not support querying "
                                  "appellate docket reports.")

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
            u'case_name': self._get_case_name(),
            u'panel': self._get_panel(),
            u'nature_of_suit': self._get_tail_by_regex("Nature of Suit"),
            u'appeal_from': self._get_tail_by_regex('Appeal From'),
            u'fee_status': self._get_tail_by_regex('Fee Status'),
            u'date_filed': self._get_tail_by_regex('Docketed', True),
            u'date_terminated': self._get_tail_by_regex('Termed', True),
            u'case_type_information': self._get_case_type_info(),
            u'originating_court_information': self._get_originating_court_info(),
        }
        data = clean_pacer_object(data)
        self._metadata = data
        return data

    @property
    def parties(self):
        """Return the party table as HTML.

        Unfortunately, the parties for appellate dockets are hard to parse. It
        can probably be done, but it's telling that this is a piece of data
        that the original RECAP authors didn't even bother with.

        The problems with parsing this data can be summarized thusly: <br>. In
        short, there is a lot of complicated data, and it's pretty much all
        separated by <br> tags instead of something that provides any kind of
        semantics. This is the kind of thing that we could do poorly, with a
        lot of effort, but that we'd always struggle to do well.

        Instead of doing that, we just collect the HTML of this section and
        return it as a string. This should *not* be considered safe HTML in
        your application.
        """
        # Grab the first table following a comment about the table.
        path = ('//comment()[contains(., "Party/Aty List")]/'
                'following-sibling::table[1]')
        try:
            party_table = self.tree.xpath(path)[0]
        except IndexError:
            return ""
        else:
            return tostring(party_table, pretty_print=True, encoding='unicode',
                            with_tail=False)

    @property
    def docket_entries(self):
        """Get the docket entries"""
        if self._docket_entries is not None:
            return self._docket_entries

        # If "View Multiple Documents" is checked, there's a form, if not, it's
        # a table. Thus, find all the trs below the first table or form after
        # the comment.
        path = ('//comment()[contains(., "DOCKET ENTRIES")]/'
                'following-sibling::*[self::table | self::form]//tr')
        docket_entry_rows = self.tree.xpath(path)

        docket_entries = []
        for row in docket_entry_rows:
            de = {}
            cells = row.xpath(u'./td')
            if len(cells) == 1:
                continue
            date_filed_str = force_unicode(cells[0].text_content())
            de[u'date_filed'] = convert_date_string(date_filed_str)
            de[u'document_number'] = self._get_document_number(cells[1])
            de[u'pacer_doc_id'] = self._get_pacer_doc_id(cells[1])
            de[u'description'] = force_unicode(cells[2].text_content())
            docket_entries.append(de)

        docket_entries = clean_pacer_object(docket_entries)
        self._docket_entries = docket_entries
        return docket_entries

    @staticmethod
    def _get_document_number( cell):
        """Get the document number"""
        text_nodes = cell.xpath('.//text()[not(parent::font)]')
        text_nodes = map(clean_string, text_nodes)
        for text_node in text_nodes:
            if text_node.isdigit():
                return text_node
        return u''

    @staticmethod
    def _get_pacer_doc_id(cell):
        urls = cell.xpath(u'.//a')
        if len(urls) == 0:
            # Entry exists but lacks a URL. Probably a minute order or similar.
            return None
        else:
            doc1_url = urls[0].xpath('./@href')[0]
            return get_pacer_doc_id_from_doc1_url(doc1_url)

    def _get_case_name(self):
        """Get the case name."""
        # The text of a cell that doesn't have bold text.
        path = '//table[contains(., "Court of Appeals Docket")]//td[not(.//b)]'
        case_name = self.tree.xpath(path)[0].text_content()
        return clean_string(harmonize(case_name))

    def _get_panel(self):
        """Get the panel information"""
        path = '//*[re:match(text(), "Panel Assignment")]/ancestor::td[1]'
        try:
            panel_table = self.tree.re_xpath(path)[0]
        except IndexError:
            # No panel table.
            return []

        panel_string = self._get_tail_by_regex('Panel:', node=panel_table)
        if panel_string in ['', "Not available"]:
            return []
        else:
            return panel_string.split()

    def _get_case_type_info(self):
        """Get the case type information and return it as a csv string"""
        path = ('//*[re:match(text(), "Case Type Information")]/'
                'ancestor::table[1]//b')
        bold_nodes = self.tree.re_xpath(path)
        case_info = []
        for node in bold_nodes:
            tail = str(node.tail).strip()
            if not any([tail == 'None', tail == 'null', tail == '-']):
                case_info.append(node.tail)
        return ', '.join(case_info)

    def _get_originating_court_info(self):
        """Get all of the originating type information as a dict."""
        ogc_table = self.tree.re_xpath('//*[re:match(text(), "Originating Court Information")]/ancestor::table[1]')[0]
        ogc_info = {}
        docket_number_node_str = ogc_table.re_xpath(
            './/*[re:match(text(), "District")]/ancestor::td[1]'
        )[0].text_content()
        m = self.docket_number_dist_regex.search(docket_number_node_str)
        if m:
            ogc_info[u'docket_number'] = m.group(1)
        else:
            # Regex didn't match. Try another way. Seems to happen when the OGC
            # is a case that wasn't in a normal district court. E.g. BIA.
            ogc_info[u'docket_number'] = docket_number_node_str.split(':')[2]

        try:
            og_court_url = ogc_table.xpath('.//a/@href')[0]
        except IndexError:
            # Happens when dockets don't link to their OGC.
            ogc_info[u'court_id'] = u''
        else:
            ogc_info[u'court_id'] = get_court_id_from_url(og_court_url)

        judge_str = self._get_tail_by_regex('Trial Judge')
        if judge_str:
            ogc_info[u'assigned_to'] = normalize_judge_string(judge_str)[0]

        ogc_info[u'court_reporter'] = self._get_tail_by_regex('Court Reporter')
        ogc_info[u'date_filed'] = self._get_tail_by_regex('Date Filed', True)
        ogc_info[u'date_disposed'] = self._get_tail_by_regex('Date Disposed', True)
        ogc_info[u'disposition'] = self._get_tail_by_regex('Disposition')

        trial_judge_str = self._get_tail_by_regex('Trial Judge')
        ogc_info[u'assigned_to'] = normalize_judge_string(trial_judge_str)[0]
        order_judge_str = self._get_tail_by_regex('Ordering Judge')
        ogc_info[u'ordering_judge'] = normalize_judge_string(order_judge_str)[0]

        date_labels = ogc_table.xpath('.//tr[last() - 1]/td//text()')
        dates = ogc_table.xpath('.//tr[last()]/td//text()')
        for label, date in zip(date_labels, dates):
            label = clean_string(label)
            date = clean_string(date)
            if label == 'Date Order/Judgment:':
                ogc_info[u'date_judgment'] = convert_date_string(date)
            if label == 'Date Order/Judgment EOD:':
                ogc_info[u'date_judgment_eod'] = convert_date_string(date)
            if label == 'Date NOA Filed:':
                ogc_info[u'date_filed_noa'] = convert_date_string(date)
            if label == "Date Rec'd COA:":
                ogc_info[u'date_received_coa'] = convert_date_string(date)
        return ogc_info

    def _get_tail_by_regex(self, regex, cast_to_date=False, node=None):
        """Search all text nodes for a string that matches the regex, then
        return the `tail`ing text.

        :param regex: A regex to search for in all text nodes.
        :param cast_to_date: Whether to convert the resulting text to a date.
        :param node: The node to search. If None, does self.tree.
        :returns unicode object: The tailing string cleaned up and optionally
        converted to a date.
        """
        node = node if node is not None else self.tree
        nodes = node.re_xpath('//*[re:match(text(), "%s")]' % regex)
        try:
            tail = clean_string(nodes[0].tail.strip())
        except (IndexError, AttributeError):
            if cast_to_date:
                return None
            else:
                return ''
        else:
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
