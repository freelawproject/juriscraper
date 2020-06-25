# coding=utf-8
from lxml import etree
from requests import Session

import six
from .docket_report import BaseDocketReport
from .docket_utils import normalize_party_types
from .utils import get_docketxml_url, get_pdf_url, is_pdf
from ..lib.judge_parsers import normalize_judge_string
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import clean_string, convert_date_string, harmonize
from ..lib.utils import clean_court_object, previous_and_next

logger = make_default_logger()

date_regex = r"[—\d\-–/]+"


class InternetArchive(BaseDocketReport):
    """A simple tool for working with the XML and PDFs on the Internet Archive
    in the RECAP collection.
    """

    CACHE_ATTRS = ["metadata", "parties", "docket_entries"]

    def __init__(self, court_id):
        super(InternetArchive, self).__init__(court_id)

        # Initialize the empty cache properties.
        self._clear_caches()
        self._metadata = None
        self._parties = None
        self._docket_entries = None

        self.session = Session()
        self.response = None
        self.tree = None
        self.parser = etree.XMLParser(recover=True)
        self.is_valid = True

    def download_pdf(self, pacer_case_id, document_number, attachment_number):
        """Download a PDF from the Internet Archive"""
        timeout = (60, 300)
        url = get_pdf_url(
            self.court_id, pacer_case_id, document_number, attachment_number
        )
        logger.info("GETting PDF at URL: %s")
        r = self.session.get(url, timeout=timeout)
        r.raise_for_status()
        if not is_pdf(r):
            logger.error("Got non-PDF data, but expected a PDF at: %s" % url)
            return None
        else:
            return r

    def query(self, pacer_case_id):
        """Download a docket XML page from the Internet Archive"""
        timeout = (60, 300)
        url = get_docketxml_url(self.court_id, pacer_case_id)
        logger.info("GETting docket XML at URL: %s")
        r = self.session.get(url, timeout=timeout)
        self.response = r
        self.parse()

    def parse(self):
        """Parse the item, but clear the cache before you do so."""
        self._clear_caches()
        self.response.raise_for_status()
        self._parse_text(self.response.text)

    def _parse_text(self, text):
        assert isinstance(
            text, six.text_type
        ), "Input must be unicode, not %s" % type(text)
        self.tree = etree.fromstring(text.encode("utf-8"), self.parser)

    @property
    def metadata(self):
        if self.is_valid is False:
            return {}

        if self._metadata is not None:
            return self._metadata

        data = {
            u"court_id": self.court_id,
            u"docket_number": self._get_str_from_tree("//docket_num"),
            u"case_name": self._get_case_name(),
            u"date_filed": self.get_datetime_from_tree(
                "//date_case_filed", cast_to_date=True
            ),
            u"date_terminated": self.get_datetime_from_tree(
                "//date_case_terminated", cast_to_date=True
            ),
            u"date_converted": None,
            u"date_discharged": None,
            u"assigned_to_str": self._get_judge("//assigned_to"),
            u"referred_to_str": self._get_judge("//referred_to"),
            u"cause": self._get_str_from_tree("//case_cause"),
            u"nature_of_suit": self._get_str_from_tree("//nature_of_suit"),
            u"jury_demand": self._get_str_from_tree("//jury_demand"),
            u"demand": "",
            u"jurisdiction": self._get_str_from_tree("//jurisdiction"),
        }
        data = clean_court_object(data)
        self._metadata = data
        return data

    @property
    def parties(self):
        """Get the party info from the XML or return it if it's cached."""
        if self._parties is not None:
            return self._parties

        party_nodes = self.tree.xpath("//party_list/party")

        parties = []
        for prev, party_node, nxt in previous_and_next(party_nodes):
            pt = self._xpath_text_0(party_node, "./type")
            extra_info = self._xpath_text_0(party_node, "./extra_info")
            name = self._xpath_text_0(party_node, "./name")
            if not name.strip():
                # Happens in adversary proceedings? See cacb_1669936.xml.
                continue
            party = {
                u"type": normalize_party_types(pt),
                u"name": name,
                u"extra_info": extra_info,
            }

            m = self.date_terminated_regex.search(extra_info)
            if m:
                party["date_terminated"] = convert_date_string(m.group(1))
            else:
                party["date_terminated"] = None

            party[u"attorneys"] = self._get_attorneys(party_node)

            if party not in parties and party != {}:
                # Sometimes there are dups in the docket. Avoid them.
                parties.append(party)

        parties = self._normalize_see_above_attorneys(parties)
        self._parties = parties
        return parties

    def _get_attorneys(self, party_node):
        attorneys = []
        for atty_node in party_node.xpath("./attorney_list/attorney"):
            attorney = {
                u"name": self._xpath_text_0(atty_node, "./attorney_name"),
                u"contact": self._xpath_text_0(atty_node, "./contact"),
            }
            roles = []
            role_str = self._xpath_text_0(atty_node, "./attorney_role")
            for role in role_str.split("\n"):
                role = role.strip()
                if not role:
                    continue
                if not any(
                    [
                        role.lower().startswith(u"bar status"),
                        role.lower().startswith(u"designation"),
                    ]
                ):
                    roles.append(role)
            attorney["roles"] = roles
            attorneys.append(attorney)
        return attorneys

    @property
    def docket_entries(self):
        if self._docket_entries is not None:
            return self._docket_entries

        de_nodes = self.tree.xpath("//document_list/document")
        docket_entries = []
        prev_date_filed = None
        for de_node in de_nodes:
            de = {
                u"document_number": de_node.xpath("./@doc_num")[0],
                u"description": self._xpath_text_0(de_node, "./long_desc"),
                u"short_description": self._xpath_text_0(
                    de_node, "./short_desc"
                ),
                u"pacer_seq_no": self._xpath_text_0(
                    de_node, "./pacer_de_seq_num"
                )
                or None,
            }
            attachment_number = de_node.xpath("./@attachment_num")[0]
            if attachment_number != "0":
                de[u"attachment_number"] = attachment_number

            date_filed_str = self._xpath_text_0(de_node, "./date_filed")
            if date_filed_str:
                # Got a date. Set it, and save it for the next item.
                try:
                    de[u"date_filed"] = convert_date_string(date_filed_str)
                except ValueError:
                    # Fails for dates like 0000-00-00
                    de[u"date_filed"] = None
                else:
                    prev_date_filed = de[u"date_filed"]
            else:
                # No date found.
                if de.get(u"attachment_number"):
                    # If it's an attachment, it probably lacks a date. Get it
                    # from the previously stored item.
                    de[u"date_filed"] = prev_date_filed
                else:
                    # If not an attachment, it's probably an old docket entry,
                    # which sometimes lack dates. Press on.
                    continue

            de[u"pacer_doc_id"] = (
                self._xpath_text_0(de_node, "./pacer_doc_id") or None
            )

            if not de[u"document_number"].isdigit():
                # Some courts put weird stuff in this column.
                continue
            docket_entries.append(de)

        docket_entries = clean_court_object(docket_entries)
        self._docket_entries = docket_entries
        return docket_entries

    def _get_judge(self, path):
        judge_str = self._get_str_from_tree(path)
        if judge_str is not None:
            return normalize_judge_string(judge_str)[0]

    def _get_case_name(self):
        case_name = self._get_str_from_tree("//case_name")
        case_name = clean_string(harmonize(case_name))
        if not case_name:
            return u"Unknown Case Title"
        return case_name
