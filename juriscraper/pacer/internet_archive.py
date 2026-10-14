from datetime import date
from types import TracebackType
from typing import NotRequired, Self

from httpx import AsyncClient, Response, Timeout
from lxml import etree
from typing_extensions import TypedDict, Unpack

from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.string_utils import (
    clean_string,
    convert_date_string,
    harmonize,
)
from juriscraper.lib.type_utils import AsyncClientOptions, GetRequestOptions
from juriscraper.lib.utils import clean_court_object, previous_and_next

from .docket_report import BaseDocketReport, DocketAttorney, DocketParty
from .docket_utils import normalize_party_types
from .utils import get_docketxml_url, get_pdf_url, is_pdf

logger = make_default_logger()


class ArchiveDocument(TypedDict):
    description: str
    pacer_seq_no: str | None
    pacer_doc_id: str | None
    document_number: NotRequired[str]
    attachment_number: NotRequired[str]
    short_description: NotRequired[str]
    date_filed: NotRequired[date | None]
    attachments: NotRequired[list["ArchiveDocument"]]


class InternetArchive(BaseDocketReport):
    """A simple tool for working with the XML and PDFs on the Internet Archive
    in the RECAP collection.
    """

    CACHE_ATTRS = ["metadata", "parties", "docket_entries"]

    def __init__(
        self, court_id: str, **kwargs: Unpack[AsyncClientOptions]
    ) -> None:
        super().__init__(court_id)

        # Initialize the empty cache properties.
        self._clear_caches()
        self._metadata: dict[str, str | date | None] | None = None
        self._parties: list[DocketParty] | None = None
        self._docket_entries: list[ArchiveDocument] | None = None
        kwargs.setdefault("http2", True)
        kwargs.setdefault("follow_redirects", True)
        kwargs.setdefault("timeout", Timeout(60, read=300))
        self.session = AsyncClient(**kwargs)
        self.response: Response | None = None
        self.tree: etree._Element | None = None
        self.parser = etree.XMLParser(recover=True)
        self.is_valid = True

    async def __aenter__(self) -> Self:
        await self.session.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.session.__aexit__(exc_type, exc_value, traceback)

    async def download_pdf(
        self,
        pacer_case_id: str | int,
        document_number: str | int,
        attachment_number: str | int | None,
        **kwargs: Unpack[GetRequestOptions],
    ) -> Response | None:
        """Download a PDF from the Internet Archive"""
        url = get_pdf_url(
            self.court_id, pacer_case_id, document_number, attachment_number
        )
        logger.info("GETting PDF at URL: %s", url)
        r = await self.session.get(url, **kwargs)
        r.raise_for_status()
        if not is_pdf(r):
            logger.error(f"Got non-PDF data, but expected a PDF at: {url}")
            return None
        else:
            return r

    async def query(
        self, pacer_case_id: str | int, **kwargs: Unpack[GetRequestOptions]
    ) -> None:
        """Download a docket XML page from the Internet Archive"""
        url = get_docketxml_url(self.court_id, pacer_case_id)
        logger.info("GETting docket XML at URL: %s", url)
        r = await self.session.get(url, **kwargs)
        self.response = r
        self.parse()

    def parse(self) -> None:
        """Parse the item, but clear the cache before you do so."""
        self._clear_caches()
        if self.response is None:
            raise ValueError("A response is required before parsing a docket.")
        self.response.raise_for_status()
        self._parse_text(self.response.text)

    def _parse_text(self, text: str) -> None:
        self._clear_caches()
        self.tree = None
        if not isinstance(text, str):
            raise TypeError(f"Input must be unicode, not {type(text)}")
        self.tree = etree.fromstring(text.encode("utf-8"), self.parser)

    @property
    def metadata(self) -> dict[str, str | date | None]:
        if self.is_valid is False:
            return {}

        if self._metadata is not None:
            return self._metadata

        data: dict[str, str | date | None] = {
            "court_id": self.court_id,
            "docket_number": self._get_str_from_tree("//docket_num"),
            "case_name": self._get_case_name(),
            "date_filed": self.get_datetime_from_tree(
                "//date_case_filed", cast_to_date=True
            ),
            "date_terminated": self.get_datetime_from_tree(
                "//date_case_terminated", cast_to_date=True
            ),
            "date_converted": None,
            "date_discharged": None,
            "assigned_to_str": self._get_judge("//assigned_to"),
            "referred_to_str": self._get_judge("//referred_to"),
            "cause": self._get_str_from_tree("//case_cause"),
            "nature_of_suit": self._get_str_from_tree("//nature_of_suit"),
            "jury_demand": self._get_str_from_tree("//jury_demand"),
            "demand": "",
            "jurisdiction": self._get_str_from_tree("//jurisdiction"),
        }
        data = clean_court_object(data)
        self._metadata = data
        return data

    @property
    def parties(self) -> list[DocketParty]:
        """Get the party info from the XML or return it if it's cached."""
        if self._parties is not None:
            return self._parties

        if self.tree is None:
            raise ValueError("Parse a docket before accessing its parties.")
        party_nodes: list[etree._Element] = self.tree.xpath(
            "//party_list/party"
        )

        parties: list[DocketParty] = []
        for _prev, party_node, _next in previous_and_next(party_nodes):
            pt = self._xpath_text_0(party_node, "./type")
            extra_info = self._xpath_text_0(party_node, "./extra_info")
            name = self._xpath_text_0(party_node, "./name")
            if not bool(name.strip()):
                # Happens in adversary proceedings? See cacb_1669936.xml.
                continue
            party: DocketParty = {
                "type": normalize_party_types(pt),
                "name": name,
                "extra_info": extra_info,
            }

            m = self.date_terminated_regex.search(extra_info)
            if m is not None:
                party["date_terminated"] = convert_date_string(m.group(1))
            else:
                party["date_terminated"] = None

            party["attorneys"] = self._get_attorneys(party_node)

            if party not in parties and party != {}:
                # Sometimes there are dups in the docket. Avoid them.
                parties.append(party)

        self._normalize_see_above_attorneys(
            attorney
            for party in parties
            for attorney in party.get("attorneys", [])
        )
        self._parties = parties
        return parties

    def _get_attorneys(
        self, party_node: etree._Element
    ) -> list[DocketAttorney]:
        attorneys: list[DocketAttorney] = []
        atty_nodes: list[etree._Element] = party_node.xpath(
            "./attorney_list/attorney"
        )
        for atty_node in atty_nodes:
            attorney: DocketAttorney = {
                "name": self._xpath_text_0(atty_node, "./attorney_name"),
                "contact": self._xpath_text_0(atty_node, "./contact"),
                "roles": [],
            }
            role_str = self._xpath_text_0(atty_node, "./attorney_role")
            for role in role_str.split("\n"):
                role = role.strip()
                if not bool(role):
                    continue
                if not any(
                    [
                        role.lower().startswith("bar status"),
                        role.lower().startswith("designation"),
                    ]
                ):
                    attorney["roles"].append(role)
            attorneys.append(attorney)
        return attorneys

    @property
    def docket_entries(self) -> list[ArchiveDocument]:
        if self._docket_entries is not None:
            return self._docket_entries

        if self.tree is None:
            raise ValueError("Parse a docket before accessing its entries.")
        de_nodes: list[etree._Element] = self.tree.xpath(
            "//document_list/document"
        )
        docket_entries: list[ArchiveDocument] = []
        for de_node in de_nodes:
            document_number = de_node.get("doc_num", "")
            if not document_number.isdigit():
                continue
            attachment_number = de_node.get("attachment_num", "0")
            pacer_doc_id = self._xpath_text_0(de_node, "./pacer_doc_id")
            pacer_seq_no = self._xpath_text_0(de_node, "./pacer_de_seq_num")
            de: ArchiveDocument = {
                "document_number": document_number,
                "description": self._xpath_text_0(
                    de_node,
                    "./short_desc"
                    if attachment_number != "0"
                    else "./long_desc",
                ),
                "pacer_doc_id": pacer_doc_id if bool(pacer_doc_id) else None,
                "pacer_seq_no": pacer_seq_no if bool(pacer_seq_no) else None,
            }
            if attachment_number != "0":
                de["attachment_number"] = attachment_number
            else:
                de["short_description"] = self._xpath_text_0(
                    de_node, "./short_desc"
                )

            date_filed_str = self._xpath_text_0(de_node, "./date_filed")
            if bool(date_filed_str):
                # Got a date. Set it, and save it for the next item.
                try:
                    de["date_filed"] = convert_date_string(date_filed_str)
                except ValueError:
                    # Fails for dates like 0000-00-00
                    de["date_filed"] = None
            else:
                # No date found.
                if not bool(de.get("attachment_number")):
                    # If not an attachment, it's probably an old docket entry,
                    # which sometimes lack dates. Press on.
                    continue

            if bool(de.get("attachment_number")):
                try:
                    last_de = docket_entries[-1]
                except IndexError:
                    continue
                if last_de.get("document_number") == document_number:
                    del de["document_number"]
                    attachments = last_de.get("attachments", [])
                    attachments.append(de)
                    last_de["attachments"] = attachments
            else:
                docket_entries.append(de)

        docket_entries = clean_court_object(docket_entries)
        self._docket_entries = docket_entries
        return docket_entries

    def _get_judge(self, path: str) -> str:
        judge_str = self._get_str_from_tree(path)
        return normalize_judge_string(judge_str)[0]

    def _get_case_name(self) -> str:
        case_name = self._get_str_from_tree("//case_name")
        case_name = clean_string(harmonize(case_name))
        if not bool(case_name):
            return "Unknown Case Title"
        return case_name
