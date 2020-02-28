# coding=utf-8
import re

from .docket_report import DocketReport
from .utils import (
    get_nonce_from_form,
    get_pacer_doc_id_from_doc1_url,
    get_pacer_seq_no_from_doc1_anchor,
)
from ..lib.judge_parsers import normalize_judge_string
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import (
    clean_string,
    convert_date_string,
    force_unicode,
    harmonize,
)
from ..lib.utils import clean_court_object, previous_and_next

logger = make_default_logger()

date_regex = r"[—\d\-–/]*"


class DocketHistoryReport(DocketReport):
    assigned_to_regex = re.compile(r"(.*),\s+presiding", flags=re.IGNORECASE)
    referred_to_regex = re.compile(r"(.*),\s+referral", flags=re.IGNORECASE)
    date_filed_regex = re.compile(r"[fF]iled:\s+(%s)" % date_regex)
    date_last_filing_regex = re.compile(
        r"last\s+filing:\s+(%s)" % date_regex, flags=re.IGNORECASE
    )
    date_filed_and_entered_regex = re.compile(
        r"& Entered:\s+(%s)" % date_regex
    )

    PATH = "cgi-bin/HistDocQry.pl"

    @property
    def data(self):
        """Get all the data back from this endpoint."""
        if self.is_valid is False:
            return {}
        data = self.metadata.copy()
        data[u"docket_entries"] = self.docket_entries
        return data

    @property
    def metadata(self):
        if self._metadata is not None:
            return self._metadata

        self._set_metadata_values()
        data = {
            u"court_id": self.court_id,
            u"docket_number": self._get_docket_number(),
            u"case_name": self._get_case_name(),
            u"date_filed": self._get_value(
                self.date_filed_regex, self.metadata_values, cast_to_date=True
            ),
            u"date_last_filing": self._get_value(
                self.date_last_filing_regex,
                self.metadata_values,
                cast_to_date=True,
            ),
            u"date_terminated": self._get_value(
                self.date_terminated_regex,
                self.metadata_values,
                cast_to_date=True,
            ),
            u"date_discharged": self._get_value(
                self.date_discharged_regex,
                self.metadata_values,
                cast_to_date=True,
            ),
            u"assigned_to_str": self._get_assigned_judge(),
            u"referred_to_str": self._get_judge(self.referred_to_regex),
        }

        data = clean_court_object(data)
        self._metadata = data
        return data

    def query(
        self,
        pacer_case_id,
        query_type="History",
        order_by="asc",
        show_de_descriptions=False,
    ):
        """Query the docket history report and return the results. Because of
        the way this works, you have to hit PACER twice. Once to get a nonce,
        and a second time to make your query.

        :param pacer_case_id: The internal PACER case ID for a case.
        :param query_type: The type of query placed. Either "History" or
        "Documents".
        :param show_de_descriptions: Whether to show docket entry descriptions
        in the report.
        :param order_by: The ordering desired for the results, either 'asc' or
        'desc'.
        :return: request response object
        """
        # Set up and sanity tests
        assert (
            self.session is not None
        ), "session attribute of DocketHistoryReport cannot be None."

        if query_type not in [u"History", u"Documents"]:
            raise ValueError(u"Invalid value for 'query_type' parameter.")
        if (
            show_de_descriptions is not True
            and show_de_descriptions is not False
        ):
            raise ValueError(u"")
        if order_by not in ["asc", "desc"]:
            raise ValueError(u"Invalid value for 'order_by' parameter.")

        logger.info(
            u"Getting nonce for docket history report with "
            u"pacer_case_id: %s" % pacer_case_id
        )
        r = self.session.get("%s?%s" % (self.url, pacer_case_id))
        nonce = get_nonce_from_form(r)

        query_params = {
            u"QueryType": query_type,
            u"sort1": order_by,
        }
        if show_de_descriptions:
            query_params["DisplayDktText"] = u"DisplayDktText"

        logger.info(
            u"Querying docket history report for case ID '%s' with "
            u"params %s and nonce %s" % (pacer_case_id, query_params, nonce)
        )

        self.response = self.session.post(
            self.url + "?" + nonce, data=query_params
        )
        self.parse()

    @property
    def docket_entries(self):
        if self._docket_entries is not None:
            return self._docket_entries

        docket_header = './/th/text()[contains(., "Description")]'
        docket_entry_rows = self.tree.xpath("//table[%s]//tr" % docket_header)[
            1:
        ]  # Skip first row

        docket_entries = []
        for row in docket_entry_rows:
            cells = row.xpath("./td")
            if len(cells) == 3:
                # Normal row, parse the document_number, date, etc.
                de = {}
                de[u"document_number"] = clean_string(cells[0].text_content())
                if de[u"document_number"] == "":
                    de[u"document_number"] = None
                anchors = cells[0].xpath(".//a")
                if len(anchors) == 1:
                    doc1_url = anchors[0].xpath("./@href")[0]
                    de[u"pacer_doc_id"] = get_pacer_doc_id_from_doc1_url(
                        doc1_url
                    )
                    de[u"pacer_seq_no"] = get_pacer_seq_no_from_doc1_anchor(
                        anchors[0]
                    )
                else:
                    # Unlinked minute entry; may or may not be numbered
                    de[u"pacer_doc_id"] = None
                    de[u"pacer_seq_no"] = None
                de[u"date_filed"] = self._get_date_filed(cells[1])
                de[u"short_description"] = force_unicode(
                    cells[2].text_content()
                )
                de[u"description"] = u""
                docket_entries.append(de)
            elif len(cells) == 1:
                # Document long description. Get it, and add it to previous de.
                desc = force_unicode(cells[0].text_content())
                label = "Docket Text: "
                if desc.startswith(label):
                    desc = desc[len(label) :]
                docket_entries[-1]["description"] = desc

        # Some docket history entries show the word "doc" instead of an entry
        # number. These items aren't on the docket itself, and so for now we
        # just skip them.
        docket_entries = [
            de
            for de in docket_entries
            if de["document_number"] is None or de["document_number"].isdigit()
        ]
        docket_entries = clean_court_object(docket_entries)
        self._docket_entries = docket_entries
        return docket_entries

    def _get_date_filed(self, cell):
        s = clean_string(cell.text_content())
        regexes = [self.date_filed_regex, self.date_filed_and_entered_regex]
        for regex in regexes:
            m = regex.search(s)
            if m:
                return convert_date_string(m.group(1))

    def _set_metadata_values(self):
        text_nodes = self.tree.xpath("//center[not(.//table)]//text()")
        values = []
        for s in text_nodes:
            s = clean_string(force_unicode(s))
            if s:
                values.append(s)
        values.append(" ".join(values))
        self.metadata_values = values

    def _get_case_name(self):
        if self.is_bankruptcy:
            # Uses both b/c sometimes the bankr. cases have a dist-style docket
            # number.
            regexes = [
                self.docket_number_dist_regex,
                self.docket_number_bankr_regex,
            ]
        else:
            regexes = [self.docket_number_dist_regex]

        matches = set()
        # Skip the last value, it's a concat of all previous values and
        # isn't needed for case name matching.
        for prev, v, nxt in previous_and_next(self.metadata_values[:-1]):
            if prev is None:
                continue
            for regex in regexes:
                match = regex.search(prev)
                if match:
                    if self.is_bankruptcy:
                        return harmonize(v)
                    for cn_regex in self.case_name_regexes:
                        cn_match = cn_regex.match(v)
                        if cn_match:
                            matches.add(cn_match.group(1))
        if len(matches) == 1:
            case_name = list(matches)[0]
        else:
            case_name = u"Unknown Case Title"
        return harmonize(case_name)

    def _get_docket_number(self):
        if self.is_bankruptcy:
            # Uses both b/c sometimes the bankr. cases have a dist-style docket
            # number.
            regexes = [
                self.docket_number_dist_regex,
                self.docket_number_bankr_regex,
            ]
        else:
            regexes = [self.docket_number_dist_regex]
        nodes = self.tree.xpath('//center//font[@size="+1"]')
        string_nodes = [s.text_content() for s in nodes]
        for regex in regexes:
            for s in string_nodes:
                match = regex.search(s)
                if match:
                    return match.group(1)

    def _get_assigned_judge(self):
        if self.is_bankruptcy:
            # Look for string like "Judge: Michael J. Fox"
            for prev, v, nxt in previous_and_next(self.metadata_values[:-1]):
                if prev is not None and re.search("Judge:", prev, flags=re.I):
                    return normalize_judge_string(v)[0]
        else:
            # Look for string like "Michael J. Fox, presiding"
            return self._get_judge(self.assigned_to_regex)
