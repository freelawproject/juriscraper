import pprint
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

    This is pretty limited metadata about the case, although it
    presents some more information for BK cases.
    """

    CACHE_ATTRS = ['metadata']

    def __init__(self, court_id, pacer_session=None):
        super(CaseQuery, self).__init__(court_id, pacer_session)
        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata = None

    @property
    def metadata(self):
        if self._metadata is not None:
            return self._metadata

        # The data we're after look like this (respacing):
        #
        # <div id="cmecfMainContent">
        #   <input type="hidden" id="cmecfMainContentScroll" value="0">
        #   <CENTER>
        #       <B><FONT SIZE=+1>1:11-cv-10230-MLW</FONT></B>
        #        Arkansas Teacher Retirement System v. State Street
        #         Corporation et al
        #     <BR>
        #       Mark L. Wolf, presiding
        #     <BR>
        #       <B>Date filed:</B> 02/10/2011
        #     <BR>
        #       <B>Date terminated:</B> 06/23/2014
        #     <BR>
        #       <B>Date of last filing:</B> 06/06/2018
        #     <BR>
        #   </CENTER>
        #
        # There's a bit more structured data in bankruptcy cases;
        # but note the extra <B></B> pair in the first line:
        #
        # <div id="cmecfMainContent">
        #   <input type="hidden" id="cmecfMainContentScroll" value="0">
        #   <CENTER>
        #       <B><FONT SIZE=+1>18-11572</FONT></B>
        #       <B></B>Nancy Jean Stevens
        #     <BR>
        #       <B>Case type:</B> bk
        #       <B>Chapter:</B> 7
        #       <B>Asset:</B> No
        #       <B>Vol: </B> v
        #       <b>Judge:</b> Frank J. Bailey
        #     <BR>
        #       <B>Date filed:</B> 04/30/2018
        #       <B>Date of last filing:</B> 06/04/2018
        #     <BR>
        #   </CENTER>
        #
        # There is some BK variation, both in terms of preence of
        # docket numbers suffixes, and how the Judge: field name
        # varies depending on the judge's chief judge status:
        #
        # <div id="cmecfMainContent">
        #   <input type="hidden" id="cmecfMainContentScroll" value="0">
        #   <CENTER>
        #       <B><FONT SIZE=+1>18-11573</FONT></B>
        #       <B></B>Sara A Taylor
        #     <BR>
        #       <B>Case type:</B> bk
        #       <B>Chapter:</B> 7
        #       <B>Asset:</B> No
        #       <B>Vol: </B> v
        #       <b>Chief Judge:</b> Melvin S. Hoffman
        #     <BR>
        #       <B>Date filed:</B> 04/30/2018
        #       <B>Date of last filing:</B> 06/06/2018
        #     <BR>
        #   </CENTER>

        # Rather than take the approach used by DocketParser of
        # searching throughout the document for a docket number by
        # regular expression, instead we take the <center> tag that follows
        # the relevant cmecfMainContent <div>, and go line-by-line,
        # delimited by <br>s. This approach is more structured:

        center = self.tree.xpath('.//div[@id="cmecfMainContent"]//center')[0]
        rows = self.redelimit_p(center, self.BR_REGEX)

        # The first row demands special handling:
        #   <B><FONT SIZE=+1>18-11572</FONT></B><B></B>Nancy Jean Stevens
        # We take the docket number from the <font> tag (the innermost tag),
        # although we could but have chosen the first <b> tag.
        docket_number = force_unicode(rows[0].find('.//font').text_content())
        # And case caption following the final <b></b> pair.
        case_name_raw = force_unicode(rows[0].find('.//b[last()]').tail)

        # Our job as a parser is to return the data, not to filter, clean,
        # amend, or "harmonize" it. However downstream often expects harmonized
        # data, so go with both.
        case_name = clean_string(harmonize(case_name_raw))

        # Iterate through the remaining rows, recognizing that the second row
        # may be special (district court), in which case it lacks the
        # <b> tag used for key/value pairs and it gives the judge's name.
        # Such as:
        #   Mark L. Wolf, presiding
        #   <B>Date filed:</B> 02/10/2011
        #   <B>Date filed:</B> 04/30/2018<B>Date of last filing:</B> 06/06/2018
        data = {}
        for i in xrange(1, len(rows)-1):
            bolds = rows[i].findall('.//b')
            if not bolds:
                if i == 1:
                    # Second row, no bold => judge name!
                    judge_role = force_unicode(rows[i].text_content())
                    PRESIDING = ", presiding"
                    assert judge_role.endswith(PRESIDING), \
                        ("We expected the judge's name to end with "
                         "', presiding'.")
                    data[u'judge_name'] = judge_role.rstrip(PRESIDING)
                else:
                    raise AssertionError('Line with no boldface?')
            for bold in bolds:
                boldtext = bold.text_content().strip()
                assert boldtext.endswith(':'), \
                    "Boldface fieldnames should end with colon (:)"
                field = boldtext.rstrip(':')
                cleanfield = field.lower().replace(' ', '_').decode('utf-8')

                value = bold.tail.strip()
                data[cleanfield] = force_unicode(value)

        # xxx use of dict.update() is kind of weird
        data.update({
            u'court_id': self.court_id,
            u'docket_number': docket_number,
            u'case_name': case_name,
            u'case_name_raw': case_name_raw,
        })

        # xxx: I don't think this is a good idea, it's too indiscriminate
        # data = clean_pacer_object(data)

        self._metadata = data
        return data

    @property
    def data(self):
        """Get all the data back from this endpoint.

        Don't attempt to return parties or docket_entries like the superclass
        does.
        """
        if self.is_valid is False:
            return {}

        data = self.metadata.copy()
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
