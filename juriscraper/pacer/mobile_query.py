"""Parse the mobile_query.pl ("Mobile Query" menu) result.

This provides the total number of docket entries, which is useful for alerts
"""
import pprint
import sys

from ..lib.log_tools import make_default_logger
from ..lib.utils import clean_court_object
from .docket_report import BaseDocketReport
from .reports import BaseReport

logger = make_default_logger()


class MobileQuery(BaseDocketReport, BaseReport):
    """Parse the mobile_query.pl ("Mobile Query" menu) result.

    This provides the total number of docket entries, which is useful for alerts
    """

    PATH = "cgi-bin/mobile_query.pl"

    CACHE_ATTRS = ["metadata"]

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
        # <a id="entriesLink" href="/cgi-bin/mobile_query.pl?search=dktEntry&caseid=186730&caseNum=4:06-cv-07294-PJH" data-transition="slide">
        #                             Docket Entries
        #                             <span class="ui-li-count">
        #                                 29
        #                             </span>
        #                         </a>
        # <div class="ui-title" style="padding-right: 90px; margin: .8em 0 1em 5%; font-size:14px; text-align: left">
        # Pages: 1,
        # Cost: 0.10

        ui_title = self.tree.xpath('.//div[@class="ui-title"]')[0]
        cost_raw = ui_title.text_content().strip()
        if (
            "Cost:" in cost_raw
        ):  # bad: means we were charged. Return immediately with bad news.
            cost = float(cost_raw.split("Cost: ", 1)[1])
            data = {"cost": cost, "cost_raw": cost_raw}
            self._metadata = data
            return data
        span = self.tree.xpath('.//a[@id="entriesLink"]//span')[0]
        entry_count = int(span.text_content().strip())
        data = {
            "court_id": self.court_id,
            "entry_count": entry_count,
            "cost": cost_raw,
        }

        data = clean_court_object(data)

        self._metadata = data
        return data

    def query(self, pacer_case_id):
        """Use a district court's PACER mobile query function with a known case id

        At the top of every district PACER court, there's a button that says,
        "Query". When you click that button, you can select "Mobile Query".
        It either does a query for the criteria you specify, returning a list
        of results or it returns the specific case you were looking for, including
        the number of docket entries in that case.

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
        curl 'https://ecf.cand.uscourts.gov/cgi-bin/mobile_query.pl?search=caseInfo&caseid=186730' \
        -H 'Content-Type: application/x-www-form-urlencoded' \
        -H 'Referer: https://external'\
        -H 'Cookie: CASE_NUM=4:06-cv-07294(186730); PacerSession=xxx; NextGenCSO=xxx; PacerPref=receipt=Y' \

        The important notes, from testing:
         - The CASE_NUM cookie isn't needed.
         """
        assert (
            self.session is not None
        ), "session attribute of MobileQuery cannot be None."
        assert bool(
            pacer_case_id
        ), f"pacer_case_id must be truthy, not '{pacer_case_id}'"
        logger.info(
            "Running mobile query for case id '%s' in court '%s'",
            pacer_case_id,
            self.court_id,
        )
        self.response = self.session.post(
            f"{self.url}?search=caseInfo&caseid=={pacer_case_id}"
        )
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
        print("Usage: python -m juriscraper.pacer.mobile_query filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)

    report = MobileQuery("mad")
    filepath = sys.argv[1]
    print(f"Parsing HTML file at {filepath}")
    with open(filepath) as f:
        text = f.read().decode("utf-8")
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
