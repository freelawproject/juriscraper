"""Parse the iquery.pl ("Query" menu) result.

This is pretty limited metadata about the case, although it
presents some more information for BK cases.
"""
import pprint
import re
import sys

from ..lib.log_tools import make_default_logger
from ..lib.string_utils import clean_string, force_unicode, harmonize
from ..lib.utils import clean_court_object
from .docket_report import BaseDocketReport
from .reports import BaseReport

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
        r"Only applications for admission to practice",
        r"Only requests for a Certificate of Good Standing",
        r"DO NOT POST IN THIS CASE",
        r"Control F",
    ]

    def __init__(self, court_id, pacer_session=None):
        BaseDocketReport.__init__(self, court_id)
        BaseReport.__init__(self, court_id, pacer_session)

        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata = None

    def parse(self):
        self._clear_caches()
        super().parse()

    @property
    def metadata(self):
        if self.is_valid is False:
            return {}

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
        center_path = './/div[@id="cmecfMainContent"]//center'
        try:
            center = self.tree.xpath(center_path)[0]
        except IndexError:
            # Can happen for sealed cases? We have at least one test case here.
            self._metadata = {}
            return {}

        rows = self.redelimit_p(center, self.BR_REGEX)

        # The first row demands special handling:
        #   <B><FONT SIZE=+1>18-11572</FONT></B><B></B>Nancy Jean Stevens
        # We take the docket number from the <font> tag (the innermost tag),
        # although we could but have chosen the first <b> tag.
        docket_number = self._parse_docket_number_strs(
            [rows[0].find(".//font").text_content()]
        )
        # And case caption following the final <b></b> pair.
        case_name_raw = force_unicode(rows[0].find(".//b[last()]").tail or "")

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
            "date_of_last_filing": "date_last_filing",
            "judge": "assigned_to_str",
            "plan_confirmed": "date_plan_confirmed",
            "debtor_discharged": "date_debtor_dismissed",
            "joint_debtor_discharged": "date_joint_debtor_dismissed",
        }
        for i in range(1, len(rows) - 1):
            bolds = rows[i].findall(".//b")
            if not bolds:
                line = force_unicode(rows[i].text_content())
                if not line:
                    continue

                if re.search(r"(panel [2-3]$|Probation)", line):
                    # Skip panelists after the first, skip probation
                    # assignments
                    continue

                if i <= 3:
                    # Second & third rows without bold => judge name!
                    presiding_re = re.compile(", (presiding|panel 1)$")
                    referral_re = re.compile(", referral$")
                    related_re = re.search("Related case: (.*)", line)
                    if presiding_re.search(line):
                        data["assigned_to_str"] = presiding_re.sub("", line)
                    elif referral_re.search(line):
                        data["referred_to_str"] = referral_re.sub("", line)
                    elif related_re:
                        data["related_cases_str"] = related_re.group(1)
                    else:
                        raise AssertionError(
                            f"Unable to match judge row: {line}"
                        )
                else:
                    raise AssertionError(f"Line with no boldface: '{line}'")
            for bold in bolds:
                data.update(
                    self._get_label_value_pair(bold, True, field_names)
                )

        data.update(
            {
                "court_id": self.court_id,
                "docket_number": docket_number,
                "case_name": case_name,
                "case_name_raw": case_name_raw,
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
        ), "session attribute of CaseQuery report cannot be None."
        assert bool(
            pacer_case_id
        ), f"pacer_case_id must be truthy, not '{pacer_case_id}'"
        params = {
            "UserType": "",
            "all_case_ids": pacer_case_id,
            "case_num": "foo",  # We just need *some* value here.
            "Qry_filed_from": "",
            "Qry_filed_to": "",
            "lastentry_from": "",
            "lastentry_to": "",
            "last_name": "",
            "first_name": "",
            "middle_name": "",
            "person_type": "",
        }
        logger.info(
            "Running case query for case ID '%s' in court '%s'",
            pacer_case_id,
            self.court_id,
        )
        self.response = self.session.post(f"{self.url}?1-L_1_0-1", data=params)
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
    print(f"Parsing HTML file at {filepath}")
    with open(filepath) as f:
        text = f.read().decode("utf-8")
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
