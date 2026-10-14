import datetime
import pprint
import re
import sys
from typing import TYPE_CHECKING, Literal, TypeAlias, overload

from httpx import Response
from lxml import html
from lxml.html import HtmlElement
from typing_extensions import override

from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.string_utils import (
    clean_string,
    convert_date_string,
    force_unicode,
    harmonize,
)
from juriscraper.lib.utils import clean_court_object

from .docket_report import (
    BaseDocketReport,
    DocketAttachment,
    DocketAttorney,
    DocketEntry,
)
from .reports import PacerReport, re_xpath
from .utils import (
    get_court_id_from_url,
    get_file_size_str_from_tr,
    get_input_value_from_tr,
    get_pacer_doc_id_from_doc1_url,
    is_pdf,
)

logger = make_default_logger()

if TYPE_CHECKING:
    from .http import PacerSession

AppellateParty: TypeAlias = dict[
    str, str | datetime.date | None | list[str] | list[DocketAttorney]
]


class AppellatePartyParser(BaseDocketReport, PacerReport):
    """Party and attorney HTML shared by appellate CM/ECF and ACMS."""

    def __init__(
        self, court_id: str, pacer_session: "PacerSession | None" = None
    ) -> None:
        super().__init__(court_id)
        PacerReport.__init__(self, court_id, pacer_session)

    PARTY_DATE_FIELDS = ["Terminated"]

    PARTY_FIELDS = {
        "Terminated": "date_terminated",
    }

    def _parse_party_left(self, tree: HtmlElement) -> AppellateParty:
        """Parse the LHS of an appellate HTML party block.

        This is used by both appellate CM/ECF and ACMS."""
        # Format:
        #  <tr><td valign=top width=50%>
        #  THEODORE D'APUZZO, P.A.<BR>
        #  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[...];Petitioner
        # but sometimes there are more fields in there:
        #  <tr>
        #  <td valign=top width=50%>LORETTA E. LYNCH, Attorney General<BR>
        #  <B>Terminated: </B>07/31/2017<BR>
        #  Respondent

        party: AppellateParty = {}

        name_role = self.redelimit_p(tree, self.BR_REGEX)
        count = len(name_role)
        if count < 2:
            raise ValueError(
                "Expecting 2+ <br>-delimited portions of party left-hand side."
            )

        # Name is first, Role is last
        party["name"] = force_unicode(name_role[0].text_content().strip())
        role = name_role[count - 1].text_content().strip()
        # Strip terminal comma, if present.
        role = re.sub(r",$", "", role)
        party["type"] = role

        unparsed = []
        for element in name_role[1 : count - 1]:
            # CM/ECF:
            #  <B>Terminated: </B>07/31/2017<BR>
            # ACMS:
            #  <strong>Terminated:</strong> 10/06/2023<br>
            _ = [element.find("strong"), element.find("b")]
            # See https://lxml.de/tutorial.html#elements-are-lists
            _ = [e for e in _ if e is not None]
            bold = _[0] if bool(_) else None
            if bold is not None:
                raw_field = bold.text_content().strip()
                # Remove terminal colon
                raw_field = re.sub(r":$", "", raw_field)
                # Translate field name to Juriscraper schema, if it exists
                if raw_field in self.PARTY_FIELDS:
                    field = self.PARTY_FIELDS[raw_field]
                else:
                    field = raw_field

                if raw_field in self.PARTY_DATE_FIELDS:
                    value = convert_date_string(
                        bold.tail if bold.tail is not None else ""
                    )
                else:
                    value = force_unicode(bold.tail)

                party[field] = value
            else:
                unparsed.append(element.text_content())

        if bool(unparsed):
            party["unparsed"] = unparsed

        return party

    def _parse_attorney(self, tree: HtmlElement) -> DocketAttorney | None:
        """Parse the attorney side of an appellate HTML party block.

        For CM/ECF this is the right-hand side directly.
        For ACMS, it is wrapped within a <div> that the caller iterates over.
        """

        # Performance note: _br_split() unparses and reparses
        # the element, just as redelimit_p() does in parties(). So
        # it's a bit wasteful to use both.
        attorney_lines = self._br_split(tree)
        if not bool(attorney_lines):
            return None
        # First line is the name
        name = attorney_lines.pop(0)
        if not bool(name):
            return None
        roles: list[str] = []
        contacts: list[str] = []
        for attorney_line in attorney_lines:
            # [Bracketted] lines are roles, others are contacts.
            m = re.match(r"\[(.*)\]", attorney_line)
            if m is not None:
                roles.append(m.group(1))
            else:
                contacts.append(attorney_line)
        return {"name": name, "roles": roles, "contact": "\n".join(contacts)}


class AppellateDocketParser(AppellatePartyParser):
    """Parse appellate dockets.

    These can be particularly detailed and for the most part we parse the data
    and provide it in our output. There are some exceptions:

     1. We don't parse the Prior/Current Cases table.
     2. We don't handle bankruptcy appellate panel dockets (yet)
    """

    docket_number_dist_regex = re.compile(
        r"((\d{1,2}:)?\d\d-[a-zA-Z]{1,4}-\d{1,10})"
    )

    CACHE_ATTRS = ["metadata", "parties", "docket_entries"]

    ERROR_STRINGS = PacerReport.ERROR_STRINGS + [
        r"The link to this page may not have originated from within CM/ECF.",
        r'Click on the "Accept Charges and Retrieve" button ONCE at the '
        r"bottom of this page to download the document image.",
        r'<embed width="100%" height="100%" name="plugin" id="plugin"',
        r"Access to the document you are about to view has been restricted.*"
        r"Do not allow it to be seen by unauthorized persons.",
        r'document.location\s*=\s*"https://pacer.login.uscourts.gov',
        r'http-equiv="REFRESH"',
        r"Case Number Not Found</b>",
        r"<title>404 Not Found</title>",
        r"<b>\d+ Documents are attached to this filing</b>",
    ]

    def __init__(
        self, court_id: str, pacer_session: "PacerSession | None" = None
    ) -> None:
        super().__init__(court_id, pacer_session)

        # Initialize the empty cache properties
        self._clear_caches()
        self._metadata: dict[str, object] | None = None
        self._parties: list[AppellateParty] | None = None
        self._docket_entries: list[DocketEntry] | None = None

    @property
    @override
    def url(self) -> str:
        if self.court_id == "psc":
            return (
                "https://dcecf.psc.uscourts.gov/n/beam/servlet/TransportRoom"
            )
        elif self.court_id in ["ca5", "ca7", "ca11"]:
            return (
                "https://ecf.%s.uscourts.gov/"
                "cmecf/servlet/TransportRoom" % self.court_id
            )
        else:
            return (
                "https://ecf.%s.uscourts.gov/"
                "n/beam/servlet/TransportRoom" % self.court_id
            )

    @override
    def parse(self) -> None:
        """Parse the item, but be sure to clear the cache before you do so.

        This ensures that if the DocketReport is used to parse multiple items,
        the cache is cleared in between.
        """
        self._clear_caches()
        super().parse()

    @override
    def _parse_text(self, text: str) -> None:
        self._clear_caches()
        super()._parse_text(text)

    @property
    def metadata(self) -> dict[str, object]:
        if self.is_valid is False:
            return {}

        if self._metadata is not None:
            return self._metadata

        data: dict[str, object] = {
            "court_id": self.court_id,
            "docket_number": self._parse_docket_number(),
            "case_name": self._get_case_name(),
            "panel": self._get_panel(),
            "nature_of_suit": self._get_tail_by_regex("Nature of Suit"),
            "appeal_from": self._get_appeal_from(
                self._get_tail_by_regex("Appeal From")
            ),
            "fee_status": self._get_tail_by_regex("Fee Status"),
            "date_filed": self._get_tail_by_regex("Docketed", True),
            "date_terminated": self._get_tail_by_regex("Termed", True),
            "case_type_information": self._get_case_type_info(),
            "originating_court_information": self._get_originating_court_info(),
        }
        data = clean_court_object(data)
        self._metadata = data
        return data

    def _parse_docket_number(self) -> str:
        """Parse the docket_number from the appellate report.
        :return: The docket_number.
        """

        docket_number_regex = "Docket #|Case Number"
        # Try to parse docket_number first using _get_tail_by_regex.
        if bool(docket_number := self._get_tail_by_regex(docket_number_regex)):
            return docket_number

        # If that doesn't work, fall back to parsing the docket_number wrapped
        # in a "tel:" href.
        if self.tree is None:
            raise ValueError("Parse a report before accessing its contents.")
        if not isinstance(self.tree, HtmlElement):
            raise TypeError("Expected an HTML tree for this report.")
        nodes = re_xpath(
            self.tree, f'//*[re:match(text(), "{docket_number_regex}")]'
        )
        if not bool(nodes):
            return ""

        a_node: list[HtmlElement] = nodes[0].xpath(
            "following-sibling::a[starts-with(@href, 'tel:')][1]"
        )
        if bool(a_node) and bool(a_node[0].text):
            return clean_string(a_node[0].text)

        return ""

    @property
    def parties(self) -> list[AppellateParty]:
        """Return the party table as HTML.

        Take the first table inside the first table following
        `NEW SECTION - Party/Aty List` and for each non-blank
        `<tr>`, the first `<td>` is the party and the second `<td>`
        is the atty list, with individual attorneys delimited with
        `<br><br>` (which are notional `<p>`s) and lines of an atty
        delimited by `<br>`, where the first line is the name.

        """
        if self._parties is not None:
            return self._parties

        # Grab the rows of the first nested table
        # following the comment defining this section of the report
        path = (
            '//comment()[contains(., "NEW SECTION - Party/Aty List")]/'
            "following-sibling::table[1]//table//tr"
        )

        if self.tree is None:
            raise ValueError("Parse a report before accessing its contents.")
        if not isinstance(self.tree, HtmlElement):
            raise TypeError("Expected an HTML tree for this report.")
        party_rows: list[HtmlElement] = self.tree.xpath(path)

        parties: list[AppellateParty] = []
        all_attorneys: list[DocketAttorney] = []
        for row in party_rows:
            cells: list[HtmlElement] = row.xpath(".//td")

            # Skip merged cells, such as blank dividers
            if len(cells) < 2:
                continue

            party = self._parse_party_left(cells[0])

            attorneys_block = cells[1]

            # For reference, here's how the XML defines the schema:
            # <attorney firstName="David"
            #    middleName="G."
            #    lastName="Baker"
            #    generation=""
            #    suffix=""
            #    title=""
            #    email=""
            #    fax="866-661-5328"
            #    address1="236 Huntington Ave"
            #    address2=""
            #    address3=""
            #    office=""
            #    unit=""
            #    room=""
            #    businessPhone=""
            #    personalPhone="617-367-4260"
            #    city="Boston"
            #    state="MA"
            #    zip="02115-4701"
            #    terminationDate=""
            #    noticeInfo="[COR NTC Retained]" />

            # Here's the HTML we have to work with. Note that
            # sometimes we have a "Direct:" phone (personalPhone)
            # first, but it can be omitted.  It's followed by the
            # noticeInfo, [bracketed].
            # HTML:
            #   <td width="50%" valign="top">
            #   Nicole Giuliano
            #   <br>Direct: 954-848-2940
            #   <br>[COR LD NTC Retained]
            #   <br>Giuliano Law, PA
            #   <br>500 E BROWARD BLVD STE 1710
            #   <br>FT LAUDERDALE, FL 33394
            #   <br>
            #   <br>
            #   Morgan L. Weinstein
            #   <br>[COR NTC Retained]
            #   <br>Law Office of Morgan L. Weinstein
            #   <br>Firm: 954-540-2755
            #   <br>5216 VAN BUREN ST
            #   <br>HOLLYWOOD, FL 33021
            #   </td>

            # We fixup the raw HTML by separating attorneys into <p>
            # elements, replacing <br><br> pairs.
            attorney_rows = self.redelimit_p(
                attorneys_block, r"(?i)<br\s*/?><br\s*/?>"
            )
            attorneys: list[DocketAttorney] = []
            for attorney_row in attorney_rows:
                _ = self._parse_attorney(attorney_row)
                # Don't add empty attorney objects
                if bool(_):
                    attorneys.append(_)

            party["attorneys"] = attorneys
            parties.append(party)
            all_attorneys.extend(attorneys)

        self._normalize_see_above_attorneys(all_attorneys)

        self._parties = parties
        return parties

    def _get_attachment_number(self, row: html.HtmlElement) -> int:
        """Return the attachment number for an item.

        :param row: Table row as an lxml element
        :return: Attachment number for row
        """
        return int(self._xpath_text_0(row, ".//td").strip())

    def _get_description_from_tr(self, row: html.HtmlElement) -> str:
        """Get the description from the row

        :param row: Table row
        :return: Attachment description
        """
        description_text_nodes: list[str] = row.xpath("./td[4]//text()")
        if not bool(description_text_nodes):
            # No text in the cell.
            return ""
        description = description_text_nodes[0].strip()
        return force_unicode(description)

    @staticmethod
    def _get_page_count_from_tr(tr: html.HtmlElement) -> int | None:
        """Take a row from the attachment table and return the page count as an
        int extracted from the input value.
        """
        count = get_input_value_from_tr(tr, 2, 4, " ")
        if count is not None:
            return int(count)

    @staticmethod
    def _get_file_size_bytes_from_tr(tr: html.HtmlElement) -> int | None:
        """Take a row from the attachment table and return the number of bytes
        as an int.
        """
        file_size_str = get_input_value_from_tr(tr, 3, 4, " ")
        if file_size_str is None:
            return None
        file_size = int(file_size_str)
        if file_size == 0:
            return None
        return file_size

    @staticmethod
    def _get_pacer_seq_no_from_tr(row: html.HtmlElement) -> str | None:
        """Take a row of the attachment table, and return the sequence number
        from the name attribute.
        """
        try:
            inputs: list[HtmlElement] = row.xpath(".//input")
            input = inputs[0]
        except IndexError:
            # No link in the row. Maybe its sealed.
            pass
        else:
            try:
                names: list[str] = input.xpath("./@value")
                name = names[0]
            except IndexError:
                # No onclick on this row.
                pass
            else:
                return name.split(" ")[0]

        return None

    def _get_attachments(
        self, cells: html.HtmlElement
    ) -> list[DocketAttachment]:
        rows: list[HtmlElement] = cells.xpath("./table//tr//tr")[1:]
        result: list[DocketAttachment] = []
        for row in rows:
            attachment: DocketAttachment = {
                "attachment_number": self._get_attachment_number(row),
                "description": self._get_description_from_tr(row),
                "page_count": self._get_page_count_from_tr(row),
                "file_size_str": get_file_size_str_from_tr(row),
                "pacer_doc_id": self._get_pacer_doc_id(row),
                # It may not be needed to reparse the seq_no
                # for each row, but we may as well. So far, it
                # has always been the same as the main document.
                "pacer_seq_no": self._get_pacer_seq_no_from_tr(row),
            }
            file_size_bytes = self._get_file_size_bytes_from_tr(row)
            if file_size_bytes is not None:
                attachment["file_size_bytes"] = file_size_bytes
            result.append(attachment)
        return result

    @property
    def docket_entries(self) -> list[DocketEntry]:
        """Get the docket entries"""
        if self._docket_entries is not None:
            return self._docket_entries

        # If "View Multiple Documents" is checked, there's a form, if not, it's
        # a table. Thus, find all the trs below the first table or form after
        # the comment.
        path = (
            '//comment()[contains(., "DOCKET ENTRIES")]/'
            "following-sibling::*[self::table | self::form]//tr"
        )
        if self.tree is None:
            raise ValueError("Parse a report before accessing its contents.")
        if not isinstance(self.tree, HtmlElement):
            raise TypeError("Expected an HTML tree for this report.")
        docket_entry_rows: list[HtmlElement] = self.tree.xpath(path)

        # Detect if the report was generated with "View multiple documents"
        # option enabled.
        view_multiple_documents = False
        view_selected_btn = self.tree.xpath("//input[@value='View Selected']")
        if view_selected_btn:
            view_multiple_documents = True
        docket_entries: list[DocketEntry] = []
        for row in docket_entry_rows:
            cells: list[HtmlElement] = row.xpath("./td")
            if len(cells) == 0:
                continue
            if len(cells) == 1:
                if cells[0].text_content() == "No docket entries found.":
                    break
                continue

            date_filed_str = force_unicode(cells[0].text_content())
            if (
                not bool(date_filed_str.strip())
                and view_multiple_documents
                and len(cells) >= 3
            ):
                if not bool(docket_entries):
                    raise ValueError(
                        "Attachment row has no preceding docket entry."
                    )
                last_de = docket_entries[-1]
                attachments = self._get_attachments(cells[2])
                if len(attachments) == 0:
                    continue
                last_de["attachments"] = attachments
                continue
            description = force_unicode(cells[2].text_content())
            de: DocketEntry = {
                "date_filed": convert_date_string(date_filed_str),
                "document_number": self._get_document_number(cells[1]),
                "pacer_doc_id": self._get_pacer_doc_id(cells[1]),
                "description": description,
                "date_entered": self._get_value(
                    self.date_entered_regex, description, cast_to_date=True
                ),
            }
            pacer_seq_no = self._get_pacer_seq_no(cells[1])
            if pacer_seq_no is not None:
                de["pacer_seq_no"] = pacer_seq_no
            if not bool(de["document_number"]):
                if bool(de["pacer_doc_id"]):
                    # If we lack the document number, but have
                    # the pacer ID, use it.
                    de["document_number"] = de["pacer_doc_id"]
                else:
                    # We lack both the document number and the pacer ID.
                    # Probably a minute order. No need to set either.
                    pass
            docket_entries.append(de)

        docket_entries = clean_court_object(docket_entries)
        self._docket_entries = docket_entries
        return docket_entries

    @staticmethod
    def _get_document_number(cell: HtmlElement) -> str | None:
        """Get the document number"""
        text_nodes: list[str] = cell.xpath(".//text()[not(parent::font)]")
        text_nodes = list(map(clean_string, text_nodes))
        for text_node in text_nodes:
            if text_node.isdigit():
                return text_node
        return None

    @staticmethod
    def _get_pacer_doc_id(cell: HtmlElement) -> str | None:
        urls: list[str] = cell.xpath(".//a/@href")
        if not bool(urls):
            # Entry exists but lacks a URL. Probably a minute order or similar.
            return None
        else:
            doc1_url = urls[0]
            return get_pacer_doc_id_from_doc1_url(doc1_url)

    @staticmethod
    def _get_pacer_seq_no(
        cell: html.HtmlElement,
    ) -> str | None:
        """Take a row from the attachment table and return the input value by
        index.
        """
        try:
            values: list[str] = cell.xpath(".//input/@value")
            return values[0]
        except IndexError:
            return None

    def _get_case_name(self) -> str:
        """Get the case name."""

        # 1: Find the comment defining this section of the report
        # 2: On its following-sibling axis, take the next table descendant,
        # 3: as long as there is boldface in the first row of the table.
        # 4: Within that table, take the cell that doesn't have any bold.

        path = (
            '//comment()[contains(., "NEW SECTION - Case Stub")]/'  # 1
            "following-sibling::*//table[1]"  # 2
            "[.//tr[1]//b]//"  # 3
            "td[not(.//b)]"
        )  # 4

        if self.tree is None:
            raise ValueError("Parse a report before accessing its contents.")
        if not isinstance(self.tree, HtmlElement):
            raise TypeError("Expected an HTML tree for this report.")
        nodes: list[HtmlElement] = self.tree.xpath(path)
        case_name = nodes[0].text_content()
        return clean_string(harmonize(case_name))

    def _get_panel(self) -> list[str]:
        """Get the panel information"""
        path = '//*[re:match(text(), "Panel Assignment")]/ancestor::td[1]'
        try:
            if self.tree is None:
                raise ValueError(
                    "Parse a report before accessing its contents."
                )
            if not isinstance(self.tree, HtmlElement):
                raise TypeError("Expected an HTML tree for this report.")
            panel_table = re_xpath(self.tree, path)[0]
        except IndexError:
            # No panel table.
            return []

        panel_string = self._get_tail_by_regex("Panel:", node=panel_table)
        if panel_string in ["", "Not available"]:
            return []
        else:
            return panel_string.split()

    def _get_case_type_info(self) -> str:
        """Get the case type information and return it as a csv string"""
        path = (
            '//*[re:match(text(), "Case Type Information")]/'
            "ancestor::table[1]//b"
        )
        if self.tree is None:
            raise ValueError("Parse a report before accessing its contents.")
        if not isinstance(self.tree, HtmlElement):
            raise TypeError("Expected an HTML tree for this report.")
        bold_nodes = re_xpath(self.tree, path)
        case_info = []
        for node in bold_nodes:
            tail = str(node.tail).strip()
            if not any(
                [tail == "None", tail == "null", tail == "-", tail == ""]
            ):
                case_info.append(node.tail if node.tail is not None else "")
        return ", ".join(case_info)

    def _get_originating_court_info(
        self,
    ) -> dict[str, str | datetime.date | None]:
        """Get all of the originating type information as a dict."""
        try:
            if self.tree is None:
                raise ValueError(
                    "Parse a report before accessing its contents."
                )
            if not isinstance(self.tree, HtmlElement):
                raise TypeError("Expected an HTML tree for this report.")
            ogc_table = re_xpath(
                self.tree,
                '//*[re:match(text(), "Originating Court Information")]/ancestor::table[1]',  # noqa
            )[0]
        except IndexError:
            # No originating court info.
            return {}

        td_is_none = re_xpath(
            ogc_table, './/*[re:match(text(), "None")]/ancestor::td[1]'
        )
        originating_court_rows: list[HtmlElement] = ogc_table.xpath(".//tr")
        if len(originating_court_rows) == 2 and bool(td_is_none):
            # No originating court info.
            return {}

        ogc_info: dict[str, str | datetime.date | None] = {}
        docket_number_node_str = re_xpath(
            ogc_table, './/*[re:match(text(), "District")]/ancestor::td[1]'
        )[0].text_content()
        m = self.docket_number_dist_regex.search(docket_number_node_str)
        if m is not None:
            docket_number = m.group(1)
            ogc_info["docket_number"] = docket_number
        else:
            # Regex didn't match. Try another way. Seems to happen
            # when the OGC is a case that wasn't in a normal district
            # court. E.g. BIA.
            #   <B>District: </B>BIA-1 : A999-999-999
            docket_number = docket_number_node_str.split(":")[2].strip()
            ogc_info["docket_number"] = docket_number

        # Alien numbers are somewhat like social security numbers for
        # non-citizens, and attorneys generally redact them from
        # public filings. Although FRAP 25(a)(5) / FRCP 5.2(c) only
        # require SSNs and TINs be redacted, it's not great to be
        # sharing Alien Numbers.  Unfortunately, many/most appeals
        # courts list them in the docket metadata, but it would be
        # best not to do so on CL without a paywall.
        #
        # Place them in their own field so we can restrict access to them
        if re.match(r"A[0-9-]+", docket_number) is not None:
            ogc_info["RESTRICTED_ALIEN_NUMBER"] = ogc_info.pop("docket_number")

        try:
            og_court_urls: list[str] = ogc_table.xpath(".//a/@href")
            og_court_url = og_court_urls[0]
        except IndexError:
            # Happens when dockets don't link to their OGC.
            ogc_info["court_id"] = ""
        else:
            ogc_info["court_id"] = get_court_id_from_url(og_court_url)

        judge_str = self._get_tail_by_regex("Trial Judge")
        if bool(judge_str):
            ogc_info["assigned_to"] = normalize_judge_string(judge_str)[0]

        ogc_info["court_reporter"] = self._get_tail_by_regex("Court Reporter")
        ogc_info["date_filed"] = self._get_tail_by_regex("Date Filed", True)
        ogc_info["date_disposed"] = self._get_tail_by_regex(
            "Date Disposed", True
        )
        ogc_info["disposition"] = self._get_tail_by_regex("Disposition")

        trial_judge_str = self._get_tail_by_regex("Trial Judge")
        ogc_info["assigned_to"] = normalize_judge_string(trial_judge_str)[0]
        order_judge_str = self._get_tail_by_regex("Ordering Judge")
        ogc_info["ordering_judge"] = normalize_judge_string(order_judge_str)[0]

        date_labels: list[str] = ogc_table.xpath(
            ".//tr[last() - 1]/td//text()"
        )
        dates: list[str] = ogc_table.xpath(".//tr[last()]/td//text()")
        for label, date in zip(date_labels, dates):
            label = clean_string(label)
            date = clean_string(date)
            if label == "Date Order/Judgment:":
                ogc_info["date_judgment"] = convert_date_string(date)
            if label == "Date Order/Judgment EOD:":
                ogc_info["date_judgment_eod"] = convert_date_string(date)
            # NOA: Notice of appeal
            if label == "Date NOA Filed:":
                ogc_info["date_filed_noa"] = convert_date_string(date)
            if label == "Date Rec'd COA:":
                ogc_info["date_received_coa"] = convert_date_string(date)
        return ogc_info

    @overload
    def _get_tail_by_regex(
        self,
        regex: str,
        cast_to_date: Literal[True],
        node: HtmlElement | None = ...,
    ) -> datetime.date | None: ...
    @overload
    def _get_tail_by_regex(
        self,
        regex: str,
        cast_to_date: Literal[False] = ...,
        node: HtmlElement | None = ...,
    ) -> str: ...  # Note: empty string is sent instead of `None`
    def _get_tail_by_regex(
        self,
        regex: str,
        cast_to_date: bool = False,
        node: HtmlElement | None = None,
    ) -> str | datetime.date | None:
        """Search all text nodes for a string that matches the regex, then
        return the `tail`ing text.

        :param regex: A regex to search for in all text nodes.
        :param cast_to_date: Whether to convert the resulting text to a date.
        :param node: The node to search. If None, does self.tree.
        :returns unicode object: The tailing string cleaned up and optionally
        converted to a date.
        """
        if node is None:
            if self.tree is None:
                raise ValueError(
                    "Parse a report before accessing its contents."
                )
            if not isinstance(self.tree, HtmlElement):
                raise TypeError("Expected an HTML tree for this report.")
            node = self.tree
        nodes = re_xpath(node, f'//*[re:match(text(), "{regex}")]')
        try:
            tail = nodes[0].tail
            tail = clean_string(tail.strip() if tail is not None else "")
        except (IndexError, AttributeError):
            if cast_to_date:
                return None
            else:
                return ""
        else:
            if cast_to_date:
                return convert_date_string(tail)
            return tail

    def _get_appeal_from(self, appeal_from: str) -> str:
        """Get the appeal from information"""
        if appeal_from == "null":
            return ""
        return appeal_from


class AppellateDocketReport(AppellateDocketParser):
    async def query(
        self,
        docket_number: str,
        show_docket_entries: bool = False,
        show_orig_docket: bool = False,
        show_prior_cases: bool = False,
        show_associated_cases: bool = False,
        show_panel_info: bool = False,
        show_party_atty_info: bool = False,
        show_caption: bool = False,
        date_start: datetime.date | None = None,
        date_end: datetime.date | None = None,
        output_format: str = "html",
    ) -> None:
        """
        Query PACER to get a docket report.

        For the most part, this is a straightforward report to generate
        according to the parameters below. The report can be generated as
        either HTML (the default) or XML.

        :param docket_number: Required argument indicating the docket number
        you wish to view. Example from ca1 is 10-1095
        :param show_docket_entries: Whether to show docket entries.
        :param show_orig_docket: Whether to show information about the docket
        in the lower court.
        :param show_prior_cases: Whether to show information about the prior
        cases in the lower court.
        :param show_associated_cases: Whether to show information about
        associated cases.
        :param show_panel_info: Whether to show information about the judicial
        panel, if it is available.
        :param show_party_atty_info: Whether to show information about the
        parties and attorneys.
        :param show_caption: Whether to show the full caption. E.g.

            IN RE:  GIFTY R. SAMUELS

            Debtor

            -----------------------------------------------

            GIFTY R. SAMUELS

            Appellant

            v.

            DEUTSCHE BANK NATIONAL TRUST COMPANY, as Trustee of the Argent
            Securities, Inc., Asset-Backed Pass-Through Certificates, Series
            2005-W3

            Appellee

        :param date_start: A filter for the docket entries. Only show entries
        from after this date (inclusive).
        :param date_end: A filter for the docket entries. Only show entries
        before this date (inclusive).
        :param output_format: Either xml or html.
        :return: None, but self.response is set and self.parse() is run

        Some examples of GET and POST requests follow.

        Standard GET request when you click on a docket you want after
        searching for it (this is the "summary" docket):
            Url: https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom?
            Params:
                servlet=CaseSummary.jsp
                caseNum=10-1095
                incOrigDkt=Y
                incDktEntries=Y

        POST that's sent when you request the full docket as HTML:
            Url: https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom
            Params:
                servlet=CaseSummary.jsp
                CSRF=csrf_-3765577682638124700
                caseNum=10-1095
                fullDocketReport=Y
                incOrigDkt=Y
                incPrior=Y
                incAssoc=Y
                incPanel=Y
                incPtyAty=Y
                incCaption=long
                incDktEntries=Y
                dateFrom
                dateTo
                incPdfMulti=Y
                actionType=Run+Docket+Report
            Also works as a GET:
                https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom?servlet=CaseSummary.jsp&CSRF=csrf_-3765577682638124700&caseNum=10-1095&fullDocketReport=Y&incOrigDkt=Y&incPrior=Y&incAssoc=Y&incPanel=Y&incPtyAty=Y&incCaption=long&incDktEntries=Y&dateFrom&dateTo&incPdfMulti=Y&actionType=Run+Docket+Report

        POST that's done by clicking the XML button:
            Url: https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom
            Params:
                All parameters same as above, except...
                outputXML_TXT=XML <-- added
                actionType <-- removed

        POST that's done by clicking the "Accept Charges and Retrieve" button
        that's shown to you *after* you request the XML the first time:
            Url: https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom
            Params:
                All parameters same as above, except...
                confirmCharge=y <-- Added
        """
        if self.session is None:
            raise ValueError("A PACER session is required to query a docket.")
        if not bool(docket_number):
            raise ValueError("A docket number is required.")

        if not show_docket_entries and (
            date_end is not None or bool(date_start)
        ):
            raise ValueError(
                "Cannot set date filtering on docket entries "
                "while show_docket_entries=False"
            )

        if output_format.lower() not in ["xml", "html"]:
            raise ValueError("Invalid value for output_format parameter.")

        query_params = {
            "servlet": "CaseSummary.jsp",
            "caseNum": docket_number,
        }
        if show_docket_entries:
            query_params["incDktEntries"] = "Y"
        if show_orig_docket:
            query_params["incOrigDkt"] = "Y"
        if show_prior_cases:
            query_params["incPrior"] = "Y"
        if show_associated_cases:
            query_params["incAssoc"] = "Y"
        if show_panel_info:
            query_params["incPanel"] = "Y"
        if show_party_atty_info:
            query_params["incPtyAty"] = "Y"
        if show_caption:
            query_params["incCaption"] = "long"

        if date_start is not None:
            query_params["dateFrom"] = date_start.strftime("%m/%d/%Y")
        if date_end is not None:
            query_params["dateTo"] = date_end.strftime("%m/%d/%Y")

        if output_format.lower() == "xml":
            query_params["outputXML_TXT"] = "XML"
            query_params["confirmCharge"] = "y"  # Lowercase y.
        elif output_format.lower() == "html":
            # When doing HTML, we need to do actionType param.
            query_params["fullDocketReport"] = "Y"
            query_params["actionType"] = "Run+Docket+Report"

        logger.info(
            "Querying appellate docket report for docket number '%s' "
            "with params %s",
            docket_number,
            query_params,
        )
        self.response = await self.session.get(self.url, params=query_params)
        self.parse()

    async def download_pdf(
        self, pacer_doc_id: str, pacer_case_id: str | None = None
    ) -> tuple[Response | None, str]:
        """Download a PDF from an appellate court.

        :param pacer_case_id: The case ID for the docket
        :param pacer_doc_id: The document ID for the item.
        :return: A tuple of the request.Response object containing a PDF, if
        one can be found (is not sealed, gone, etc.). And a string indicating
        the error message, if there is one or else an empty string.

        This is a functional curl command to get a PDF (though the cookies have
        been changed to protect the innocent):

        curl 'https://ecf.ca1.uscourts.gov/n/beam/servlet/TransportRoom' \
            -H 'Referer: https://external' \
            -H 'Cookie: CMECFASESSIONID=xzy; NextGenCSO=abc;  PacerSession=def' \
            --data 'servlet=ShowDoc&incPdfHeader=Y&incPdfHeaderDisp=Y&dls_id=00116008873&pacer=t' \
            --output test.pdf

        This is done with the following HTML and JavaScript:

        <form name="AccCharge" action="TransportRoom" method="post">
            <input name="servlet" value="ShowDoc" type="hidden">
            <input name="CSRF" value="csrf_-7746865752981737651" type="hidden">
            <input name="incPdfHeader" value="N" type="hidden">
            <input name="incPdfHeaderDisp" value="Y" checked="" type="checkbox">Show PDF Header
            <input name="dls_id" value="00116008873" type="hidden">
            <input name="caseId" value="30442" type="hidden">
            <input name="recp" value="" type="hidden"><input name="pacer" value="t" type="hidden">
            <input value="Accept Charges and Retrieve" onclick="doSubmit()" type="button">
        </form>

        var today = new Date();
        function doSubmit() {
            document.AccCharge.recp.value=today.getTime()+"";

            if (document.forms[0].incPdfHeaderDisp.checked) {
                document.forms[0].incPdfHeader.value = 'Y';
            } else {
                document.forms[0].incPdfHeader.value = 'N';
            }

            document.AccCharge.submit();
        }

        Note that although the recp parameter is created by the JS, and so you
        might think it's important, it doesn't seem to do anything that we've
        identified and so is ignored below.
        # noqa
        """
        if self.session is None:
            raise ValueError("A PACER session is required to download a PDF.")
        query_params = {
            "servlet": "ShowDoc",
            "incPdfHeader": "Y",
            "incPdfHeaderDisp": "Y",
            "dls_id": pacer_doc_id,
            "pacer": "t",  # Not sure what this does, but it's required.
        }
        if bool(pacer_case_id):
            query_params["caseId"] = pacer_case_id
        logger.info(
            "GETting PDF at URL: %s with params: %s", self.url, query_params
        )
        r = await self.session.get(self.url, params=query_params)
        r.raise_for_status()

        if b"Documents are attached to this filing" in r.content:
            error_message = (
                "Unable to download PDF. "
                "An attachment page was returned instead."
            )
            return None, error_message

        if not is_pdf(r):
            return None, "Unable to download PDF."

        logger.info(
            "Got PDF binary data for document #%s in court %s",
            pacer_doc_id,
            self.court_id,
        )
        return r, ""


def _main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.appellate_docket filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)
    report = AppellateDocketReport(
        "ca9"
    )  # Court ID is only needed for querying.
    filepath = sys.argv[1]
    print(f"Parsing HTML file at {filepath}")
    with open(filepath) as f:
        text = f.read()
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
