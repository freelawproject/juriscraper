"""Search for cases and parse the iquery.pl search results.

This lets you look up cases and parse results. Note that the classes here are
similar but distinct from CaseQuery, which is used with a particular case and
returns a menu of options as a result.

In the cases, we look up search results by name, date, etc.
"""

import pprint
import sys
from collections.abc import Sequence
from datetime import date
from typing import TYPE_CHECKING, Never, TypeAlias

from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.string_utils import (
    clean_string,
    convert_date_string,
    force_unicode,
    harmonize,
)
from juriscraper.lib.utils import clean_court_object

from .docket_report import BaseDocketReport
from .reports import BaseReport
from .utils import get_pacer_case_id_from_nonce_url

logger = make_default_logger()

if TYPE_CHECKING:
    from .http import PacerSession

CaseResults: TypeAlias = list[dict[str, str | date | None]] | dict[str, Never]


class BaseCaseQueryAdvanced(BaseDocketReport[CaseResults], BaseReport):
    """Base query for both district and bankruptcy queries."""

    PATH = "cgi-bin/iquery.pl"

    CACHE_ATTRS = ["metadata"]

    def __init__(
        self, court_id: str, pacer_session: "PacerSession | None" = None
    ) -> None:
        super().__init__(court_id)
        BaseReport.__init__(self, court_id, pacer_session)

        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata: CaseResults | None = None

    @override
    def parse(self) -> None:
        self._clear_caches()
        super().parse()

    @override
    def _parse_text(self, text: str) -> None:
        self._clear_caches()
        super()._parse_text(text)

    @property
    def metadata(self) -> CaseResults:
        raise NotImplementedError("Subclasses must parse case search results.")

    @property
    @override
    def data(self) -> CaseResults:
        """Get all the data back from this endpoint.

        Don't attempt to return parties or docket_entries like the superclass
        does.
        """
        if self.is_valid is False:
            return {}

        return self.metadata

    @staticmethod
    def get_text_for_cell(cell: HtmlElement) -> str:
        """Return the text within a <td>"""
        return force_unicode(cell.text_content().strip())

    def get_date_for_cell(self, cell: HtmlElement) -> date | None:
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
    @override
    def metadata(self) -> CaseResults:
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

        if self.tree is None:
            raise ValueError("Parse a report before accessing its contents.")
        if not isinstance(self.tree, HtmlElement):
            raise TypeError("Expected an HTML tree for this report.")
        table_rows: list[HtmlElement] = self.tree.xpath(
            '//table//tr[@class="rowBackground1" or @class="rowbackground2"]'
        )
        data: list[dict[str, str | date | None]] = []

        for table_row in table_rows:
            cells: list[HtmlElement] = table_row.xpath("./td")
            if len(cells) == 7:
                # There are person and case results. Eliminate the first and
                # sixth cells to normalize with tables that lack person results
                # This is a hack that makes debugging harder. Better would be
                # to sniff the header row.
                del cells[5]
                del cells[0]

            docket_number, docket_number_components = (
                self._parse_docket_number_strs(
                    [self.get_text_for_cell(cells[0])]
                )
            )
            row_data: dict[str, str | date | None] = {
                "docket_number": docket_number,
                "case_name": clean_string(
                    harmonize(self.get_text_for_cell(cells[1]))
                ),
                "chapter": self.get_text_for_cell(cells[2]),
                "date_filed": self.get_date_for_cell(cells[3]),
                "date_closed": self.get_date_for_cell(cells[4]),
            }
            hrefs: list[str] = cells[0].xpath(".//@href")
            href = hrefs[0]
            row_data["pacer_case_id"] = get_pacer_case_id_from_nonce_url(href)
            # Include the docket_number components.
            row_data.update(docket_number_components)

            data.append(row_data)

        data = clean_court_object(data)

        self._metadata = data
        return data

    async def query(
        self,
        name_last: str = "",
        name_first: str = "",
        name_middle: str = "",
        person_type: str = "",
        filed_from: date | None = None,
        filed_to: date | None = None,
        last_entry_from: date | None = None,
        last_entry_to: date | None = None,
        natures_of_suit: str | Sequence[str | int] = "",
    ) -> None:
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
        if self.session is None:
            raise ValueError(
                "session attribute of DocketReport cannot be None."
            )
        if (filed_from is None) != (filed_to is None):
            raise ValueError(
                "Both or neither of filing date fields must be complete."
            )
        if (last_entry_from is None) != (last_entry_to is None):
            raise ValueError(
                "Both or neither of last entry date fields must be complete."
            )

        # PACER only allows so many days per query. Exceed this threshold and
        # you get an error message and zero results.
        max_days = 31
        max_days_msg = (
            "PACER has a %s day limit on date filters. "
            "Narrow your search." % max_days
        )
        if (
            filed_from is not None
            and filed_to is not None
            and (filed_to - filed_from).days + 1 >= max_days
        ):
            raise ValueError(max_days_msg)
        if (
            last_entry_from is not None
            and last_entry_to is not None
            and (last_entry_to - last_entry_from).days + 1 >= max_days
        ):
            raise ValueError(max_days_msg)

        params = {}
        if filed_from is not None:
            params["filed_from"] = filed_from.strftime("%m/%d/%Y")
        if filed_to is not None:
            params["filed_to"] = filed_to.strftime("%m/%d/%Y")
        if last_entry_from is not None:
            params["lastentry_from"] = last_entry_from.strftime("%m/%d/%Y")
        if last_entry_to is not None:
            params["lastentry_to"] = last_entry_to.strftime("%m/%d/%Y")

        params.update(
            {
                # Name fields
                "last_name": name_last,
                "first_name": name_first,
                "middle_name": name_middle,
                "person_type": person_type,
            }
        )
        logger.info("Running advanced case query with params '%s'", params)
        self.response = await self.session.post(
            f"{self.url}?1-L_1_0-1", data=params
        )
        self.parse()


class CaseQueryAdvancedDistrict(BaseCaseQueryAdvanced):
    """iQuery.pl for district cases

    Not yet implemented. Unfortunately both the query parameters needed for the
    query() method and the results parsed by the metadata() method are unique
    across district and bankruptcy.
    """

    def __new__(cls) -> Never:
        raise NotImplementedError("This object is a stub.")

    async def query(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError("This object is a stub")


def _main() -> None:
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
    print(f"Parsing HTML file at {filepath}")
    with open(filepath, "rb") as f:
        text = f.read().decode("utf-8")
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
