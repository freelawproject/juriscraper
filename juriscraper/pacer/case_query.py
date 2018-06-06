import pprint
import re
import sys

from .docket_report import BaseDocketReport
from .reports import BaseReport
# from .utils import clean_pacer_object
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import clean_string, harmonize, \
    force_unicode

logger = make_default_logger()


class CaseQuery(BaseDocketReport, BaseReport):
    """Parse the iquery.pl ("Query" menu) result.

    This is pretty limited metadata.
    """

    docket_number_dist_regex = re.compile(
        r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})")

    # PATH = 'n/beam/servlet/TransportRoom'
    CACHE_ATTRS = ['metadata']

    def __init__(self, court_id, pacer_session=None):
        super(CaseQuery, self).__init__(court_id, pacer_session)
        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata = None
        self._parties = None
        self._docket_entries = None

    def parse(self):
        """Parse the item, but be sure to clear the cache before you do so.

        This ensures that if the DocketReport is used to parse multiple items,
        the cache is cleared in between.
        """
        self._clear_caches()
        super(CaseQuery, self).parse()

    @property
    def metadata(self):
        if self._metadata is not None:
            return self._metadata

        center = self.tree.xpath('.//div[@id="cmecfMainContent"]//center')[0]
        rows = self.redelimit_p(center, r'(?i)<br\s*/?>')

        # First row is special
        docket_number = force_unicode(rows[0].find('.//font').text_content())
        raw_case_name = force_unicode(rows[0].find('.//b[last()]').tail)
        judge_name = None

        # Remainder are <b>Field name:</b> value
        # Except the 2nd row might or might not be.
        data = {}
        for i in xrange(1, len(rows)):
            bolds = rows[i].findall('.//b')
            if bolds is None and i == 1:
                # Second row, no bold => judge name!
                judge_name = force_unicode(rows[i].text_content()
                                           .rstrip(", presiding"))
            for bold in bolds:
                field = bold.text_content().strip().rstrip(':')
                cleanfield = field.lower().replace(' ', '_').decode('utf-8')
                value = bold.tail.strip()
                data[cleanfield] = force_unicode(value)

        case_name = clean_string(harmonize(raw_case_name))

        data.update({
            u'court_id': self.court_id,
            u'docket_number': docket_number,
            u'case_name': case_name,
            u'raw_case_name': raw_case_name,
        })
        if judge_name is not None:
            data[u'judge_name'] = judge_name,

        # I don't think this is a good idea, it's too indiscriminate
        # data = clean_pacer_object(data)

        self._metadata = data
        return data

    @property
    def data(self):
        """Get all the data back from this endpoint."""
        if self.is_valid is False:
            return {}

        data = self.metadata.copy()
        # data[u'parties'] = self.parties
        # data[u'docket_entries'] = self.docket_entries
        return data


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.case_query filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)
    report = CaseQuery(
        # xxx that's a lie, court id appears in output
        'mad')  # Court ID is only needed for querying.
    filepath = sys.argv[1]
    print("Parsing HTML file at %s" % filepath)
    with open(filepath, 'r') as f:
        text = f.read().decode('utf-8')
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)
