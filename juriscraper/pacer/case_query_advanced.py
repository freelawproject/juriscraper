"""Search for cases and parse the iquery.pl search results.

This lets you look up cases and parse results. Note that the classes here are
similar but distinct from CaseQuery, which is used with a particular case and
returns a menu of options as a result.

In the cases, we look up search results by name, date, etc.
"""
import pprint
import sys

from .docket_report import BaseDocketReport
from .reports import BaseReport
from .utils import get_pacer_case_id_from_nonce_url
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import (
    clean_string,
    convert_date_string,
    force_unicode,
    harmonize,
)
from ..lib.utils import clean_court_object

logger = make_default_logger()


class BaseCaseQueryAdvanced(BaseDocketReport, BaseReport):
    """Base query for both district and bankruptcy queries.
    """

    PATH = "cgi-bin/iquery.pl"

    CACHE_ATTRS = ["metadata"]

    def __init__(self, court_id, pacer_session=None):
        BaseDocketReport.__init__(self, court_id)
        BaseReport.__init__(self, court_id, pacer_session)

        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata = None

    def parse(self):
        self._clear_caches()
        super(BaseCaseQueryAdvanced, self).parse()

    @property
    def data(self):
        """Get all the data back from this endpoint.

        Don't attempt to return parties or docket_entries like the superclass
        does.
        """
        if self.is_valid is False:
            return {}

        return self.metadata

    @staticmethod
    def get_text_for_cell(cell):
        """Return the text within a <td>"""
        return force_unicode(cell.text_content().strip())

    def get_date_for_cell(self, cell):
        """Return a parsed date within a <td>"""
        s = self.get_text_for_cell(cell)
        try:
            return convert_date_string(s)
        except ValueError:
            # Happens when the value isn't a date, like when it's "N/A", say.
            return None


class CaseQueryAdvancedBankruptcy(BaseCaseQueryAdvanced):
    """iQuery.pl for bankruptcy cases"""

    @property
    def metadata(self):
        if self.is_valid is False:
            return {}

        if self._metadata is not None:
            return self._metadata

        # The data we're after look like this (re-spacing):
        #
        # <TR class=rowBackground1>
        #     <TD VALIGN=center>PacifiCorp (pty) <br> (1 case)</TD>
        #     <TD NOWRAP VALIGN=center><A
        #             HREF="iquery.pl?440916540563012-L_1_0-0-12612">01-30923</A>
        #     </TD>
        #     <TD VALIGN=center>Pacific Gas and Electric Co.</TD>
        #     <TD VALIGN=center> 11</TD>
        #     <TD VALIGN=center> 04/06/01</TD>
        #     <TD VALIGN=center> Creditor</TD>
        #     <TD VALIGN=center>N / A</TD>
        # </TR>
        #
        # With the following columns (in bankruptcy):
        #    1. Name  (we skip this for now)
        #    2. Case Number
        #    3. Case Title
        #    4. Chapter / Lead BK case
        #    5. Date Filed
        #    6. Party Role (we skip this row for now)
        #    7. Date Closed
        #
        # Columns 1 and 6 are not always present, and so as a first pass below
        # we just nuke them. They're not that important to us now anyway. But
        # none would deny this is a hackish way to normalize the results.

        table_rows = self.tree.xpath(
            '//table//tr[@class="rowBackground1" or '
            '@class="rowbackground2"]'
        )
        data = []

        for table_row in table_rows:
            cells = table_row.xpath("./td")
            if len(cells) == 7:
                # There are person and case results. Eliminate the first and
                # sixth cells to normalize with tables that lack person results
                # This is a hack that makes debugging harder. Better would be
                # to sniff the header row.
                del cells[5]
                del cells[0]

            row_data = {
                "docket_number": self.get_text_for_cell(cells[0]),
                "case_name": clean_string(
                    harmonize(self.get_text_for_cell(cells[1]))
                ),
                "chapter": self.get_text_for_cell(cells[2]),
                "date_filed": self.get_date_for_cell(cells[3]),
                "date_closed": self.get_date_for_cell(cells[4]),
            }
            href = cells[0].xpath(".//@href")[0]
            row_data["pacer_case_id"] = get_pacer_case_id_from_nonce_url(href)

            data.append(row_data)

        data = clean_court_object(data)

        self._metadata = data
        return data

    def query(
        self,
        name_last="",
        name_first="",
        name_middle="",
        person_type="",
        filed_from=None,
        filed_to=None,
        last_entry_from=None,
        last_entry_to=None,
        natures_of_suit="",
    ):
        """Use a bankruptcy court's PACER query function to look up cases

        At the top of every district PACER court, there's a button that says,
        "Query". When you click that button, it either does a query for the
        criteria you specify, returning a list of results or it returns the
        specific case you were looking for, including metadata and a list of
        reports you can run on that case.

        This method only supports the use case where you are looking up
        criteria. For the other use case, please see the CaseQuery object.
        SSN and Tax ID filtering not yet implemented.

        :param name_last: The last name to look up.
        :param name_first: The first name to look up.
        :param name_middle: The middle name to look up.
        :param person_type: What type the person is. See PACER for valid
        entries.
        :param filed_from: The date filed entry for the earliest possible
        filing (inclusive).
        :type filed_from: datetime.date
        :param filed_to: The date filed value for the latest possible filing
        (inclusive).
        :type filed_to: datetime.date
        :param last_entry_from: The earliest date that the last entry on the
        docket can be from. I think.
        :type last_entry_from: datetime.date
        :param last_entry_to: The latest date that the last entry on the docket
        can be from. I think.
        :type last_entry_to: datetime.date
        :param natures_of_suit: A Python list of nature of suit numbers that to
        use for filtering. (See PACER for values.)

        :return None: Instead, sets self.response attribute and runs
        self.parse()
        """
        assert (
            self.session is not None
        ), "session attribute of DocketReport cannot be None."
        assert all([filed_from, filed_to]) or not any(
            [filed_from, filed_to]
        ), "Both or neither of filing date fields must be complete."
        assert all([last_entry_from, last_entry_to]) or not any(
            [last_entry_from, last_entry_to]
        ), "Both or neither of last entry date fields must be complete."

        # PACER only allows so many days per query. Exceed this threshold and
        # you get an error message and zero results.
        max_days = 31
        max_days_msg = (
            "PACER has a %s day limit on date filters. "
            "Narrow your search." % max_days
        )
        if filed_from:
            assert (filed_to - filed_from).days + 1 < max_days, max_days_msg
        if last_entry_from:
            assert (
                last_entry_to - last_entry_from
            ).days + 1 < max_days, max_days_msg

        params = {}
        if filed_from:
            params[u"filed_from"] = filed_from.strftime(u"%m/%d/%Y")
        if filed_to:
            params[u"filed_to"] = filed_to.strftime(u"%m/%d/%Y")
        if last_entry_from:
            params[u"lastentry_from"] = last_entry_from.strftime(u"%m/%d/%Y")
        if last_entry_to:
            params[u"lastentry_to"] = last_entry_to.strftime(u"%m/%d/%Y")

        params.update(
            {
                # Name fields
                u"last_name": name_last,
                u"first_name": name_first,
                u"middle_name": name_middle,
                u"person_type": person_type,
            }
        )
        logger.info(u"Running advanced case query with params '%s'", params)
        self.response = self.session.post(self.url + "?1-L_1_0-1", data=params)
        self.parse()


class CaseQueryAdvancedDistrict(BaseCaseQueryAdvanced):
    """iQuery.pl for district cases

    Not yet implemented. Unfortunately both the query parameters needed for the
    query() method and the results parsed by the metadata() method are unique
    across district and bankruptcy.
    """

    def __init__(self):
        raise NotImplementedError("This object is a stub.")

    def query(self, *args, **kwargs):
        raise NotImplementedError("This object is a stub")


def _main():
    if len(sys.argv) != 2:
        print(
            "Usage: python -m juriscraper.pacer.case_query_advanced filepath"
        )
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)

    # Court ID is only needed for querying. Actual
    # parsed value appears in output
    report = CaseQueryAdvancedBankruptcy("mad")
    filepath = sys.argv[1]
    print("Parsing HTML file at %s" % filepath)
    with open(filepath, "r") as f:
        text = f.read().decode("utf-8")
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
