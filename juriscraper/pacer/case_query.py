"""Parse the iquery.pl ("Query" menu) result.

This is pretty limited metadata about the case, although it
presents some more information for BK cases.
"""
import pprint
import re
import sys

from six.moves import range

from .docket_report import BaseDocketReport
from .reports import BaseReport
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import clean_string, force_unicode, harmonize
from ..lib.utils import clean_court_object

logger = make_default_logger()


class CaseQuery(BaseDocketReport, BaseReport):
    """Parse the iquery.pl ("Query" menu) result.

    This is pretty limited metadata about the case, although it
    presents some more information for BK cases.
    """

    PATH = "cgi-bin/iquery.pl"

    CACHE_ATTRS = ["metadata"]

    ERROR_STRINGS = BaseReport.ERROR_STRINGS + [
        r"Case not found\.",
    ]

    def __init__(self, court_id, pacer_session=None):
        super(CaseQuery, self).__init__(court_id, pacer_session)
        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata = None

    def parse(self):
        self._clear_caches()
        super(CaseQuery, self).parse()

    @property
    def metadata(self):
        if self._metadata is not None:
            return self._metadata

        # The data we're after look like this (re-spacing):
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
        # There is some BK variation, both in terms of presence of
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
        docket_number = force_unicode(rows[0].find(".//font").text_content())
        # And case caption following the final <b></b> pair.
        case_name_raw = force_unicode(rows[0].find(".//b[last()]").tail)

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
        field_names = {
            u"date_of_last_filing": u"date_last_filing",
            u"judge": u"assigned_to_str",
            u"plan_confirmed": u"date_plan_confirmed",
            u"debtor_discharged": u"date_debtor_dismissed",
        }
        for i in range(1, len(rows) - 1):
            bolds = rows[i].findall(".//b")
            if not bolds:
                line = force_unicode(rows[i].text_content())
                if re.search(r'panel [2-3]$', line):
                    # For now we only care about the first panelist
                    continue

                if i == 1:
                    # Second row, no bold => judge name!
                    presiding_re = re.compile(", (presiding|panel 1)$")
                    assert presiding_re.search(line), (
                        "We expected the judge's name to end with "
                        "'presiding or panel'. Instead, it's: '%s'" % line
                    )
                    data[u"assigned_to_str"] = presiding_re.sub('', line)
                elif i == 2:
                    # Third row, no bold => referred judge name!
                    referral_re = re.compile(", referral$")
                    assert referral_re.search(line), (
                        "We expected the referred judge's name to end "
                        "with ', referral'. Instead it's: '%s'" % line
                    )
                    data[u"referred_to_str"] = referral_re.sub('', line)
                else:
                    raise AssertionError("Line with no boldface: '%s'" % line)
            for bold in bolds:
                data.update(
                    self._get_label_value_pair(bold, True, field_names)
                )

        data.update(
            {
                u"court_id": self.court_id,
                u"docket_number": docket_number,
                u"case_name": case_name,
                u"case_name_raw": case_name_raw,
            }
        )

        data = clean_court_object(data)

        self._metadata = data
        return data

    def query(self, pacer_case_id):
        """Use a district court's PACER query function with a known case ID

        At the top of every district PACER court, there's a button that says,
        "Query". When you click that button, it either does a query for the
        criteria you specify, returning a list of results or it returns the
        specific case you were looking for, including metadata and a list of
        reports you can run on that case.

        While there is utility in both of these result types, this method only
        supports the use case where you know the pacer_case_id in advance, and
        are expecting only one result in return. This method does *not* support
        parsing the search results that the Query button can return. That use
        case is supposed by the CaseQueryAdvancedBankruptcy and
        CaseQueryAdvancedDistrict objects.

        :param pacer_case_id: A pacer_case_id for a case to lookup.
        :return None: Instead, sets self.response attribute and runs
        self.parse()
        """

        """
        This is an example of a query that could be sent, and which we're
        attempting to replicate:
            curl 'https://ecf.ord.uscourts.gov/cgi-bin/iquery.pl?1-L_1_0-1'
                -H 'Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7Sz5UdWuoi5TbtDj'
                -H 'Referer: https://external'
                -H 'Cookie: CASE_NUM=6:16-cv-01710(128548); PacerSession=xxx; PacerPref=receipt=Y'
                --data-binary $'------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="UserType"\r\n\r\n\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="all_case_ids"\r\n\r\n128548\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="case_num"\r\n\r\n6:16-cv-1710\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="Qry_filed_from"\r\n\r\n\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="Qry_filed_to"\r\n\r\n\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="lastentry_from"\r\n\r\n\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="lastentry_to"\r\n\r\n\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="last_name"\r\n\r\n\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="first_name"\r\n\r\n\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="middle_name"\r\n\r\n\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj\r\nContent-Disposition: form-data;
                    name="person_type"\r\n\r\n\r\n------WebKitFormBoundary7Sz5UdWuoi5TbtDj--\r\n'

        The important notes, from testing:
         - The CASE_NUM cookie isn't needed.
         - The case_num parameter needs a value; any value will do.
         - As usual, the ?1-L_1_0-1 business in the URL is needed
        """
        assert (
            self.session is not None
        ), "session attribute of DocketReport cannot be None."
        assert bool(pacer_case_id), (
            "pacer_case_id must be truthy, not '%s'" % pacer_case_id
        )
        params = {
            u"UserType": "",
            u"all_case_ids": pacer_case_id,
            u"case_num": "foo",  # We just need *some* value here.
            u"Qry_filed_from": "",
            u"Qry_filed_to": "",
            u"lastentry_from": "",
            u"lastentry_to": "",
            u"last_name": "",
            u"first_name": "",
            u"middle_name": "",
            u"person_type": "",
        }
        logger.info(
            u"Running case query for case ID '%s' in court '%s'",
            pacer_case_id,
            self.court_id,
        )
        self.response = self.session.post(self.url + "?1-L_1_0-1", data=params)
        self.parse()

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


def _main():
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.case_query filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)

    # Court ID is only needed for querying. Actual
    # parsed value appears in output
    report = CaseQuery("mad")
    filepath = sys.argv[1]
    print("Parsing HTML file at %s" % filepath)
    with open(filepath, "r") as f:
        text = f.read().decode("utf-8")
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
