"""Classes for querying PACER's Written Opinion Report (WrtOpRpt.pl),
which is free.
"""
import pprint
import sys

from ..lib.date_utils import make_date_range_tuples
from ..lib.html_utils import (
    clean_html,
    fix_links_in_lxml_tree,
    get_html_parsed_text,
    set_response_encoding,
)
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import clean_string, convert_date_string, harmonize
from ..pacer.utils import (
    get_nonce_from_form,
    get_pacer_case_id_from_nonce_url,
    get_pacer_doc_id_from_doc1_url,
    reverse_goDLS_function,
)
from .docket_report import BaseDocketReport
from .reports import BaseReport

logger = make_default_logger()


class FreeOpinionReport(BaseReport):
    """An object for querying and parsing the free opinion report."""

    EXCLUDED_COURT_IDS = ["casb", "innb", "miwb", "ohsb"]
    VALID_SORT_PARAMS = ("date_filed", "case_number")

    def __init__(self, court_id, pacer_session=None):
        self.responses = []
        self.trees = []
        super().__init__(court_id, pacer_session)

    @property
    def url(self):
        if self.court_id == "ohnd":
            return "https://ecf.ohnd.uscourts.gov/cgi-bin/OHND_WrtOpRpt.pl"
        else:
            return (
                f"https://ecf.{self.court_id}.uscourts.gov/cgi-bin/WrtOpRpt.pl"
            )

    def query(self, start, end, sort="date_filed", day_span=7):
        """Query the Free Opinions report one day at a time.

        :param start: a date object representing the date you want to start at.
        :param end: a date object representing the date you want to end at.
        :param sort: the order you wish the results to be in, either
        `date_filed` or `case_number`.
        :param day_span: The number of days to query at a time. Defaults to one
        week.
        """
        if self.court_id in self.EXCLUDED_COURT_IDS:
            logger.error(
                "Cannot get written opinions report from '%s'. It is "
                "not provided by the court or is in disuse.",
                self.court_id,
            )
            return

        dates = make_date_range_tuples(start, end, gap=day_span)
        responses = []
        for _start, _end in dates:
            _start = _start.strftime("%m/%d/%Y")
            _end = _end.strftime("%m/%d/%Y")
            # Iterate one day at a time. Any more and PACER chokes.
            logger.info(
                "Querying written opinions report for '%s' between %s "
                "and %s, ordered by %s",
                self.court_id,
                _start,
                _end,
                sort,
            )

            # Get the first page, grab the nonce, and submit using that.
            response = self.session.get(self.url)
            nonce = get_nonce_from_form(response)
            logger.info("Got nonce of %s", nonce)

            data = {
                "filed_from": _start,
                "filed_to": _end,
                "ShowFull": "1",
                "Key1": self._normalize_sort_param(sort),
                "all_case_ids": "0",
            }
            response = self.session.post(f"{self.url}?{nonce}", data=data)
            responses.append(response)

        self.responses = responses
        self.parse()

    def parse(self):
        """Using a list of responses, parse out useful information and return
        it as a list of dicts.
        """
        # Reset self.trees before each run or successive runs will add more and
        # more rows.
        self.trees = []
        for response in self.responses:
            response.raise_for_status()
            set_response_encoding(response)
            text = clean_html(response.text)
            tree = get_html_parsed_text(text)
            tree.rewrite_links(fix_links_in_lxml_tree, base_href=response.url)
            self.trees.append(tree)

    def _parse_text(self, text):
        """Parse the HTML as unicode text and set self.tree

        This is a particularly critical method when running tests, which pull
        from local disk instead of from a query response. This is also used
        when data comes from a source other than self.query() (such as a user
        upload). This method should probably be made public as .parse_text().

        :param text: A unicode object
        :return: None
        """
        assert isinstance(
            text, str
        ), f"Input must be unicode, not {type(text)}"
        text = clean_html(text)
        self.tree = get_html_parsed_text(text)
        self._strip_bad_html_tags_insecure(text)
        self.tree.rewrite_links(fix_links_in_lxml_tree, base_href=self.url)
        self.trees.append(self.tree)

    @property
    def data(self):
        results = []
        for tree in self.trees:
            opinion_count = int(
                tree.xpath(
                    '//b[contains(text(), "Total number of '
                    'opinions reported")]'
                )[0].tail
            )
            if opinion_count == 0:
                continue
            rows = tree.xpath("(//table)[1]//tr[position() > 1]")
            for row in rows:
                if results:
                    # If we have results already, pass the previous result to
                    # the FreeOpinionRow object.
                    row = FreeOpinionRow(row, results[-1], self.court_id)
                else:
                    row = FreeOpinionRow(row, {}, self.court_id)
                results.append(row.data)
        logger.info(
            "Parsed %s results from written opinions report at %s",
            len(results),
            self.court_id,
        )
        return results

    def _normalize_sort_param(self, sort):
        if sort == "date_filed":
            return "de_date_filed"
        elif sort == "case_number":
            return "cs_sort_case_numb"
        else:
            raise ValueError(
                "Invalid sort parameter. Value must be one of: %s"
                % ", ".join(self.VALID_SORT_PARAMS)
            )


class FreeOpinionRow(BaseDocketReport):
    """A row in the Free Opinions report.

    For the most part this is fairly straightforward, however eight courts have
    a different type of report that only has four columns instead of the usual
    five (hib, deb, njb, ndb, ohnb, txsb, txwb, vaeb), and a couple courts
    (areb & arwb) have five columns, but are designed more like the four column
    variants.

    The second complication is that cells in the row change position based on
    the sort order of the report. If the report is ordered by date, then the
    first cell is the date. If the report is ordered by case number, then the
    first cell is the case number and case name.

    In general, what we do is detect the column count, and sort order early on
    and then work from there.
    """

    def __init__(self, element, last_good_row, court_id):
        """Initialize the object.

        last_good_row should be a dict representing the values from
        the previous row in the table. This is necessary because the
        report skips the case name if it's the same for two cases in a
        row. For example:

        Joe v. Volcano | 12/31/2008 | 128 | The first doc from case | More here
                       | 12/31/2008 | 129 | The 2nd doc from case   | More here

        By having the values from the previous row, we can be sure to be able
        to complete the empty cells.

        """
        super().__init__(court_id)
        self._metadata = None
        self.element = element
        self.last_good_row = last_good_row
        self.court_id = court_id
        self._column_count = self._get_column_count()
        self._sort_order = self._detect_sort_order()
        self.docket_number = self._parse_docket_number_strs(
            [self.get_docket_number()]
        )

    def __str__(self):
        return f"<FreeOpinionRow in {self.court_id}>\n{self.data}"

    @property
    def metadata(self):
        if self._metadata is not None:
            return self._metadata

        results = self.get_pacer_case_id_and_pacer_seq_no()
        data = {
            "court_id": self.court_id,
            "pacer_case_id": results[0],
            "pacer_seq_no": results[1],
            "docket_number": self.docket_number,
            "case_name": self.get_case_name(),
            "date_filed": self.get_date_filed(),
            "pacer_doc_id": self.get_pacer_doc_id(),
            "document_number": self.get_document_number(),
            "description": self.get_description(),
            "nature_of_suit": self.get_nos(),
            "cause": self.get_cause(),
        }

        self._metadata = data
        return data

    @property
    def data(self):
        """Get all the data back from this endpoint."""
        data = self.metadata.copy()
        return data

    def _get_column_count(self):
        return len(self.element.xpath("./td"))

    def _detect_sort_order(self):
        """Detect whether the report is ordered by case number or by date filed.

        If the report is ordered by date filed, you'll have a table row like:

            12/31/2008 | Joe v. Volcano | 128 | The first doc | More here

        If it's ordered by case name, it'll be like:

            Joe v. Volcano | 12/31/2008 | 128 | The first doc | More here

        The case name is always a link, so the simple way to do this
        is to check if there's a link in the second cell of the
        row. If so, it's ordered by date_filed. Else, by
        case_number. Note that the first cell is often blank.
        """
        if len(self.element.xpath("./td[2]//@href")) > 0:
            return "date_filed"
        else:
            return "case_number"

    def get_pacer_case_id_and_pacer_seq_no(self):
        """Get the pacer_case_id and pacer_seq_no values for a document.

        Both come from the link to the document, if it has an onclick
        attribute.
        """
        # It's tempting to get this value from the URL in the first
        # cell, but that URL can sometimes differ from the URL used in
        # the goDLS function.  When that's the case, the download
        # fails.
        try:
            onclick = self.element.xpath("./td[3]//@onclick")[0]
        except IndexError:
            pass
        else:
            if "goDLS" in onclick:
                # Sometimes the onclick is something else, like in insb's free
                # opinion report.
                go_dls_parts = reverse_goDLS_function(onclick)
                return go_dls_parts["caseid"], go_dls_parts["de_seq_num"]

        # No onclick, onclick isn't a goDLS link, etc. Try second format.
        if self._sort_order == "case_number":
            try:
                # This tends to work in the bankr. courts.
                href = self.element.xpath("./td[1]//@href")[0]
            except IndexError:
                logger.info(
                    "No content provided in first cell of row. Using "
                    "last good row for pacer_case_id, docket_number, "
                    "and case_name."
                )
                last_row = self.last_good_row
                return last_row["pacer_case_id"], last_row["pacer_seq_no"]
        elif self._sort_order == "date_filed":
            href = self.element.xpath("./td[2]//@href")[0]
        return get_pacer_case_id_from_nonce_url(href), None

    def get_docket_number(self):
        try:
            if self._sort_order == "case_number":
                cell = self.element.xpath("./td[1]//a")[0]
            else:
                cell = self.element.xpath("./td[2]//a")[0]
        except IndexError:
            # No content in the cell.
            return self.last_good_row["docket_number"]
        else:
            s = cell.text_content().strip()

        if self._column_count == 4 or self.court_id in ["areb", "arwb"]:
            # In this case s will be something like:
            #   14-90018 Stewart v. Kauanui
            # Split on the first space, left is docket number, right
            # is case name.
            return s.split(" ", 1)[0]
        else:
            return s

    def get_case_name(self):
        if self._sort_order == "case_number":
            cell = self.element.xpath("./td[1]")[0]
        else:
            cell = self.element.xpath("./td[2]")[0]
        s = cell.text_content().strip()
        if not s:
            return clean_string(harmonize(self.last_good_row["case_name"]))

        if self._column_count == 4 or self.court_id in ["areb", "arwb"]:
            # See note in docket number
            try:
                return clean_string(harmonize(s.split(" ", 1)[1]))
            except IndexError:
                # No case name, but a docket number is provided.
                return "Case name unknown"
        else:
            try:
                return clean_string(
                    harmonize(cell.xpath(".//b")[0].text_content())
                )
            except IndexError:
                logger.warning(
                    "Unable to get case name for %s in %s.",
                    self.docket_number,
                    self.court_id,
                )
                return "Case name unknown"

    def get_date_filed(self):
        if self._sort_order == "case_number":
            path = "./td[2]//text()"
        elif self._sort_order == "date_filed":
            path = "./td[1]//text()"
        s = self.element.xpath(path)[0]
        if not s.strip() and self._sort_order == "date_filed":
            # Empty cell, return the previous value.
            return self.last_good_row["date_filed"]
        else:
            return convert_date_string(s)

    def get_pacer_doc_id(self):
        doc1_url = self.element.xpath("./td[3]//@href")[0]
        return get_pacer_doc_id_from_doc1_url(doc1_url)

    def get_document_number(self):
        return self.element.xpath("./td[3]//text()")[0]

    def get_description(self):
        return self.element.xpath("./td[4]")[0].text_content()

    def get_nos(self):
        if self._column_count == 4:
            return ""
        try:
            return self.element.xpath(
                "./td[5]/i[contains(./text(), " '"NOS")]'
            )[0].tail.strip()
        except IndexError:
            return ""

    def get_cause(self):
        if self._column_count == 4:
            return ""
        try:
            return self.element.xpath(
                "./td[5]/i[contains(./text(), " '"Cause")]'
            )[0].tail.strip()
        except IndexError:
            return ""


def _main():
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.docket_report filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)
    report = FreeOpinionReport(
        "cand", None
    )  # Court ID is only needed for querying.
    filepath = sys.argv[1]
    print(f"Parsing HTML file at {filepath}")
    with open(filepath) as f:
        text = f.read()
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
