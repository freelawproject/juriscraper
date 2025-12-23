import re
from datetime import date, datetime
from enum import Enum
from functools import cached_property
from itertools import chain, groupby
from typing import TypedDict
from urllib.parse import parse_qs, urlparse

from lxml import html
from lxml.html import HtmlElement

from juriscraper.abstract_parser import AbstractParser
from juriscraper.lib.html_utils import (
    clean_html,
    fix_links_but_keep_anchors,
    get_all_text,
    parse_table,
)
from juriscraper.lib.string_utils import (
    FILE_SIZE_RE,
    clean_string,
    harmonize,
    size_string_to_bytes,
)


class CourtID(Enum):
    """
    Standardized IDs for Texas courts. Created by prefixing "texas_" to the ID
    that TAMES uses. Used by consumers to deterministically identify courts.
    """

    UNKNOWN = "texas_unknown"
    SUPREME_COURT = "texas_cossup"
    COURT_OF_CRIMINAL_APPEALS = "texas_coscca"
    FIRST_COURT_OF_APPEALS = "texas_coa01"
    SECOND_COURT_OF_APPEALS = "texas_coa02"
    THIRD_COURT_OF_APPEALS = "texas_coa03"
    FOURTH_COURT_OF_APPEALS = "texas_coa04"
    FIFTH_COURT_OF_APPEALS = "texas_coa05"
    SIXTH_COURT_OF_APPEALS = "texas_coa06"
    SEVENTH_COURT_OF_APPEALS = "texas_coa07"
    EIGHTH_COURT_OF_APPEALS = "texas_coa08"
    NINTH_COURT_OF_APPEALS = "texas_coa09"
    TENTH_COURT_OF_APPEALS = "texas_coa10"
    ELEVENTH_COURT_OF_APPEALS = "texas_coa11"
    TWELFTH_COURT_OF_APPEALS = "texas_coa12"
    THIRTEENTH_COURT_OF_APPEALS = "texas_coa13"
    FOURTEENTH_COURT_OF_APPEALS = "texas_coa14"
    FIFTEENTH_COURT_OF_APPEALS = "texas_coa15"


COA_ORDINAL_MAP = {
    "first": CourtID.FIRST_COURT_OF_APPEALS,
    "second": CourtID.SECOND_COURT_OF_APPEALS,
    "third": CourtID.THIRD_COURT_OF_APPEALS,
    "fourth": CourtID.FOURTH_COURT_OF_APPEALS,
    "fifth": CourtID.FIFTH_COURT_OF_APPEALS,
    "sixth": CourtID.SIXTH_COURT_OF_APPEALS,
    "seventh": CourtID.SEVENTH_COURT_OF_APPEALS,
    "eighth": CourtID.EIGHTH_COURT_OF_APPEALS,
    "ninth": CourtID.NINTH_COURT_OF_APPEALS,
    "tenth": CourtID.TENTH_COURT_OF_APPEALS,
    "eleventh": CourtID.ELEVENTH_COURT_OF_APPEALS,
    "twelfth": CourtID.TWELFTH_COURT_OF_APPEALS,
    "thirteenth": CourtID.THIRTEENTH_COURT_OF_APPEALS,
    "fourteenth": CourtID.FOURTEENTH_COURT_OF_APPEALS,
    "fifteenth": CourtID.FIFTEENTH_COURT_OF_APPEALS,
    "1st": CourtID.FIRST_COURT_OF_APPEALS,
    "2nd": CourtID.SECOND_COURT_OF_APPEALS,
    "3rd": CourtID.THIRD_COURT_OF_APPEALS,
    "4th": CourtID.FOURTH_COURT_OF_APPEALS,
    "5th": CourtID.FIFTH_COURT_OF_APPEALS,
    "6th": CourtID.SIXTH_COURT_OF_APPEALS,
    "7th": CourtID.SEVENTH_COURT_OF_APPEALS,
    "8th": CourtID.EIGHTH_COURT_OF_APPEALS,
    "9th": CourtID.NINTH_COURT_OF_APPEALS,
    "10th": CourtID.TENTH_COURT_OF_APPEALS,
    "11th": CourtID.ELEVENTH_COURT_OF_APPEALS,
    "12th": CourtID.TWELFTH_COURT_OF_APPEALS,
    "13th": CourtID.THIRTEENTH_COURT_OF_APPEALS,
    "14th": CourtID.FOURTEENTH_COURT_OF_APPEALS,
    "15th": CourtID.FIFTEENTH_COURT_OF_APPEALS,
}


def coa_name_to_court_id(coa_name: str) -> CourtID:
    """
    Takes in the name of a Texas Court of Appeals and returns the corresponding
    CourtID.

    :param coa_name: The name of the Court of Appeals, extracted from the
    docket page.

    :return: The CourtID corresponding to the given Court of Appeals name.
    """
    ordinal = coa_name.split()[0]
    return COA_ORDINAL_MAP[ordinal.lower()]


class TexasAppealsCourt(TypedDict):
    """
    Schema for Texas appeals court details.

    :ivar case_number: The case number of the appeals court case.
    :ivar case_url: The URL to the appeals court case.
    :ivar disposition: The disposition of the appeals court case.
    :ivar opinion_cite: The opinion citation.
    :ivar district: The appeals court district.
    :ivar justice: The name of the appeals court judge.
    """

    case_number: str
    case_url: str
    disposition: str
    opinion_cite: str
    district: str
    justice: str


def _parse_appeals_court(tree: HtmlElement) -> TexasAppealsCourt:
    """
    Helper function to parse appeals court information and construct a
    `TexasAppealsCourt` instance. Used by `TexasSupremeCourtScraper` and
    `TexasCourtOfCriminalAppealsScraper`.

    :return: Extracted appeals court information.
    """
    container = tree.find(
        './/*[@id="ctl00_ContentPlaceHolder1_divCOAInfo"]/div/div/div[2]'
    )
    info_container = container.find(
        './/*[@id="ctl00_ContentPlaceHolder1_pnlCOA"]'
    )
    # Texas gives the judge their own child element all to themselves for some
    # reason.
    judge_container = container.find(
        './/*[@id="ctl00_ContentPlaceHolder1_pnlCOAJudge"]'
    )
    if judge_container is None:
        judge_container = []
    case_info = {
        clean_string(row.find(".//*[1]").text_content()): row.find(".//*[2]")
        for row in (list(info_container) + list(judge_container))
    }
    justice_node = case_info.get("COA Justice")

    return TexasAppealsCourt(
        case_number=clean_string(case_info["COA Case"].text_content()),
        case_url=case_info["COA Case"].find(".//a").get("href"),
        disposition=clean_string(case_info["Disposition"].text_content()),
        opinion_cite=clean_string(case_info["Opinion Cite"].text_content()),
        district=clean_string(case_info["COA District"].text_content()),
        justice=clean_string(
            justice_node.text_content() if justice_node is not None else ""
        ),
    )


class TexasCaseParty(TypedDict):
    """
    Schema for Texas case party details.

    This class is used as a utility to define the necessary attributes for a
    party and allow type hints.

    :ivar name: The name associated with the party.
    :ivar type: The type of the party (respondent, petitioner, etc.).
    :ivar representatives: A list of representatives associated with the party.
    """

    name: str
    type: str
    representatives: list[str]


class TexasTrialCourt(TypedDict):
    """
    Schema for Texas Trial Court details.

    This class is a `TypedDict` that defines the schema for representing a
    Texas Trial Court. It is used as a utility for safety and type hints.

    The `judge`, `reporter`, and `punishment` attributes may be empty (most
    often the `punishment` field will be empty in civil cases), and it is up to
    the consumer to handle those cases.

    :ivar name: The name of the court.
    :ivar county: The county where the court is located.
    :ivar judge: The name of the presiding judge in the court.
    :ivar case: Specific case identification or name handled by this court.
    :ivar reporter: The name of the court reporter for the case.
    :ivar punishment: The punishment or outcome decided by the court in the
    case.
    """

    name: str
    county: str
    judge: str
    case: str
    reporter: str
    punishment: str


class TexasCaseDocument(TypedDict):
    """
    Schema for Texas case document details.

    :ivar document_url: The URL of the document.
    :ivar media_id: The `media_id` parameter extracted from `document_url`.
    :ivar media_version_id: The `media_version_id` parameter extracted from
    `document_url`.
    :ivar description: The name of the document (may be empty).
    """

    document_url: str
    media_id: str
    media_version_id: str
    description: str
    file_size_bytes: int
    file_size_str: str


class TexasDocketEntry(TypedDict):
    """
    Schema for Texas docket entry details.

    :ivar date: The date of the docket entry.
    :ivar type: The type of the docket entry (e.g., "Notice of appeal
    received").
    :ivar attachments: Any documents associated with the docket entry.
    """

    date: date
    type: str
    attachments: list[TexasCaseDocument]


class TexasCaseEvent(TexasDocketEntry):
    """
    Extension of `TexasDocketEntry` to handle rows from the "Case Events"
    table.

    :ivar disposition: The value of the "Disposition" column (e.g., "Filing
    granted")
    """

    disposition: str


class TexasAppellateBrief(TexasDocketEntry):
    """
    Extension of `TexasDocketEntry` to handle rows from the "Appellate Briefs"
    table.

    :ivar description: The value of the "Description" column (e.g., "Relator")
    """

    description: str


class TexasCommonData(TypedDict):
    """
    Schema for data common to all Texas dockets.

    This class is a `TypedDict` that defines the schema for representing data
    common to all Texas dockets. It is used as a utility for safety and type
    hints.

    :ivar court_id: The ID of the court this docket is from.
    :ivar docket_number: The docket number of the case.
    :ivar case_name: The shortened and normalized name of the case.
    :ivar case_name_full: The full name of the case.
    :ivar date_filed: The date the case was filed.
    :ivar case_type: The type of case.
    :ivar parties: A list of parties involved in the case and their associated
    representatives.
    :ivar trial_court: Information about the trial court handling the case was
    appealed from.
    :ivar case_events: A list of case events (e.g., filing of the case, notice
    of appeal received).
    :ivar appellate_briefs: A list of briefs filed in the case.
    """

    court_id: str
    docket_number: str
    case_name: str
    case_name_full: str
    date_filed: date
    case_type: str
    parties: list[TexasCaseParty]
    trial_court: TexasTrialCourt
    case_events: list[TexasCaseEvent]
    appellate_briefs: list[TexasAppellateBrief]


DOCKET_NUMBER_REGEXES = [
    re.compile(r"\d{2}-\d{4}"),  # Supreme Court
    re.compile(r"\d{2}-\d{2}-\d{5}-\w{2}"),  # Court of Appeals
    re.compile(r"\w{2}-\d{4}-\d{2}"),  # Court of Criminal Appeals
]


class TexasCommonScraper(AbstractParser[TexasCommonData]):
    """
    A scraper for extracting data common to all Texas dockets (Supreme Court,
    Court of Criminal Appeals, and Court of Appeals).

    Extracts the following data:
    - Docket number
    - Date filed
    - Case type
    - Case parties (name, type, and representatives)
    - Trial court information (court name, county, judge, case number,
    reporter, and punishment)

    :ivar tree: The HTML tree of the docket page.
    :ivar events: The "Case Events" table data extracted with `parse_table`.
    :ivar briefs: The "Appellate Briefs" table data extracted with
    `parse_table`.
    :ivar is_valid: `True` if the HTML tree has been successfully parsed by
    calling `_parse_text`, `False` otherwise.
    """

    date_format = "%m/%d/%Y"
    base_url = "https://search.txcourts.gov"

    def __init__(self, court_id: str = CourtID.UNKNOWN.value) -> None:
        super().__init__(court_id)
        self.tree: HtmlElement = HtmlElement()
        self.events: dict[str, list[HtmlElement]] = {}
        self.briefs: dict[str, list[HtmlElement]] = {}
        self.case_data: dict[str, str] = {}
        self.is_valid: bool = False

    def _parse_text(self, text: str) -> None:
        """
        Takes in a string, cleans it, and parses it into an HTML tree. If the
        tree is parsed without raising an exception, the `is_valid` attribute
        is set to `True`.

        :param text: The raw HTML string.
        """
        self.tree = html.fromstring(clean_html(text))
        self.tree.rewrite_links(
            fix_links_but_keep_anchors, base_href=self.base_url
        )
        briefs_table = self.tree.find(
            './/table[@id="ctl00_ContentPlaceHolder1_grdBriefs_ctl00"]'
        )
        events_table = self.tree.find(
            './/table[@id="ctl00_ContentPlaceHolder1_grdEvents_ctl00"]'
        )
        if events_table is None:
            raise ValueError("Case events table not found.")
        if briefs_table is None:
            raise ValueError("Appellate briefs table not found.")
        self.events = parse_table(events_table)
        self.briefs = parse_table(briefs_table)
        self.case_data = self._extract_case_data()
        self.is_valid = True

    @property
    def data(self) -> TexasCommonData:
        """
        Extract parsed data from an HTML tree. This property returns the
        `TexasCommonData`
        object.

        :raises ValueError: If the `_parse_text` method has not been called
        yet.

        :return: Parsed data.
        """
        if not self.is_valid:
            raise ValueError("HTML tree has not been parsed yet.")

        data = TexasCommonData(
            court_id=CourtID.UNKNOWN.value,
            docket_number=self.docket_number,
            date_filed=self._parse_date_filed(),
            case_type=self._parse_case_type(),
            parties=self.parties,
            trial_court=self._parse_trial_court(),
            case_events=self._parse_case_events(),
            appellate_briefs=self._parse_appellate_briefs(),
            case_name=self.case_name,
            case_name_full=self.case_name_full,
        )
        return data

    @cached_property
    def docket_number(self) -> str:
        """
        The docket number of the case.
        """
        return self._parse_docket_number()

    @staticmethod
    def _extract_case_data_name(name_element: HtmlElement) -> str:
        """
        Helper method used by _extract_case_data to clean the titles of entries
        in the case data table. First calls the clean_string method, then
        removes all characters that are not whitespace or alphanumeric and
        converts to lowercase.
        """
        name = "".join(get_all_text(name_element))
        return re.sub(r"[^\s\w]", "", clean_string(name)).lower()

    def _extract_case_data(self) -> dict[str, str]:
        """
        Helper method to extract the case information at the top of the page
        into a dictionary. After cleaning text, the keys are the text on the
        left of the table and the values are the text on the right. Will fail
        if `_parse_text` has not yet been called.

        :return: Dictionary containing the case information.
        """
        parent = self.tree.find('.//*[@id="case"]/..')
        coa_parent = parent.find(
            './/*[@id="ctl00_ContentPlaceHolder1_COAOnly"]'
        )
        children = parent.iterfind('.//*[@class="row-fluid"]')

        if coa_parent is not None:
            children = chain(
                children, coa_parent.iterfind('.//*[@class="row-fluid"]')
            )

        return {
            self._extract_case_data_name(child.find(".//*[1]")): clean_string(
                get_all_text(child.find(".//*[2]"))
            )
            for child in children
        }

    BUSINESS_AND_TITLE_STRIP_RE = re.compile(
        "|".join(
            [
                r"(?:(,\s+)?" + r"\.?".join(list(acronym)) + r"\.?)"
                for acronym in ["LLC", "MD", "PA"]
            ]
        ),
        re.IGNORECASE,
    )

    def _find_party_in_case_name(self, party_name: str) -> tuple[int, int]:
        """
        Finds the start and end indices of the party name in the case name.

        Useful in instances where a name appears as "last, first" in the
        parties list and "first last" in the case name.

        :param party_name: The party name to search for.

        :return: Index of the party name in the case name.
        """
        party_name = harmonize(party_name).lower()
        party_name_parts = [part.strip() for part in party_name.split(",")]
        if len(party_name_parts) == 1:
            start = self.case_name_full.lower().find(party_name_parts[0])
            end = start + len(party_name_parts[0])
            return start, end
        # If there are two parts, this might be someone's name written as Last,
        # First
        if len(party_name_parts) == 2:
            # Try to find First Last
            maybe_first_last = f"{party_name_parts[1]} {party_name_parts[0]}"
            start = self.case_name_full.lower().find(maybe_first_last)
            if start >= 0:
                end = start + len(maybe_first_last)
                return start, end

            # There do not appear to be instances of a person's name written
            # as Last, First in the case name in TAMES, so we don't check for
            # that case.

        # If we failed to find the party name in the case name by treating
        # it as a person's name, assume that the comma indicates a list of
        # parties
        # Strip out acronyms like LLC, MD, and PA so they don't clutter things
        party_name_parts = filter(
            lambda part: not self.BUSINESS_AND_TITLE_STRIP_RE.fullmatch(part),
            party_name_parts,
        )
        party_name_parts = [
            part.removeprefix("the ").strip() for part in party_name_parts
        ]
        party_name_parts_indexed = [
            (self.case_name_full.lower().find(part), part)
            for part in party_name_parts
        ]
        party_name_parts_indexed.sort(key=lambda x: x[0])
        start = party_name_parts_indexed[0][0]
        end = party_name_parts_indexed[-1][0] + len(
            party_name_parts_indexed[-1][1]
        )
        return start, end

    def _make_short_party_name(
        self, name_part: str, parties: list[TexasCaseParty]
    ) -> str:
        """
        Creates a shortened version of the party name based on the given list
        of parties.

        Sometimes multiple parties to a case are listed in the same entry on
        TAMES so this method

        1. Chooses the shortest party name between the list of parties and the
        long case name (these are often different)
        2. Attempts to find and return the first party name in a string by
        splitting on semicolons. Some cases also list multiple parties in one
        entry separated by commas, but this is significantly more difficult to
        handle due to cases such as "lastname, firstname" and "company, LLC".

        :param name_part: The initial part of the case name to process.
        :param parties: A list of parties from which to determine the shortened
        name.

        :return: The shortened party name derived from the input parameters.
        """
        if len(parties) == 0:
            return name_part
        if len(parties) == 1:
            if len(parties[0]["name"]) < len(name_part):
                return parties[0]["name"]
            return name_part
        semi = name_part.find(";")
        if semi > 0:
            return name_part[:semi]

        party_indices = [
            self._find_party_in_case_name(party["name"]) for party in parties
        ]
        party_indices.sort(key=lambda x: x[0])
        start, end = next(
            indices for indices in party_indices if indices[0] >= 0
        )
        return self.case_name_full[start:end]

    @cached_property
    def case_name_full(self) -> str:
        """
        The unshortened name of the case as it appears on TAMES.
        """
        name_part_1 = self.case_data["style"]
        name_part_2 = self.case_data["v"]
        if len(name_part_2) == 0:
            return harmonize(name_part_1)
        return harmonize(f"{name_part_1} v. {name_part_2}")

    @cached_property
    def case_name(self) -> str:
        """
        A (possibly) shortened version of the case name created using some
        heuristics. Useful to make cases easier to search and match.
        """
        name_part_1 = self.case_data["style"]
        name_part_2 = self.case_data["v"]
        if len(name_part_2) == 0:
            return harmonize(name_part_1)

        grouped_parties = {}
        for k, g in groupby(self.parties, lambda party: party["type"]):
            if k in grouped_parties:
                grouped_parties[k].extend(list(g))
            else:
                grouped_parties[k] = list(g)

        first_parties = list(
            chain(
                grouped_parties.get("Petitioner", []),
                grouped_parties.get("Appellant", []),
            )
        )
        second_parties = list(
            chain(
                grouped_parties.get("Respondent", []),
                grouped_parties.get("Appellee", []),
            )
        )

        name_short_part_1 = self._make_short_party_name(
            name_part_1, first_parties
        )
        name_short_part_2 = self._make_short_party_name(
            name_part_2, second_parties
        )
        return harmonize(f"{name_short_part_1} v. {name_short_part_2}")

    def _parse_docket_number(self) -> str:
        """
        Extracts the docket number from the HTML tree. Will fail if
        `_parse_text` has not yet been called.

        :raises ValueError: If the docket number format is not recognized.

        :return: Docket number.
        """
        docket_number = self.case_data["case"]
        for docket_number_regex in DOCKET_NUMBER_REGEXES:
            if docket_number_regex.fullmatch(docket_number):
                return docket_number
        raise ValueError(f"Unrecognized docket number format: {docket_number}")

    def _parse_date_filed(self) -> date:
        """
        Extracts the date the case was filed from the HTML tree and parses it
        into a `datetime` object from mm/dd/yyyy format. Will fail if
        `_parse_text` has not yet been called.

        :return: Date filed
        """
        date_string = self.case_data["date filed"]
        return datetime.strptime(date_string, self.date_format).date()

    def _parse_case_type(self) -> str:
        """
        Extracts the case type from the HTML tree. Will fail if `_parse_text`
        has not yet been called.

        :return: Case Type
        """
        return self.case_data["case type"]

    @cached_property
    def parties(self) -> list[TexasCaseParty]:
        return self._parse_parties()

    def _parse_parties(self) -> list[TexasCaseParty]:
        """
        Extracts the parties from the HTML tree. Multiline entries in the
        "Representative" column will be treated as if each line is an
        individual representative for the relevant party. Will fail if
        `_parse_text` has not yet been called.

        :return: Parties
        """
        table = self.tree.find(
            './/table[@id="ctl00_ContentPlaceHolder1_grdParty_ctl00"]'
        )
        parties = parse_table(table)
        n_parties = len(parties["Party"])

        return [
            TexasCaseParty(
                name=clean_string(parties["Party"][i].text_content()),
                type=clean_string(parties["PartyType"][i].text_content()),
                representatives=[
                    clean_string(text)
                    for text in parties["Representative"][i].xpath(".//text()")
                ],
            )
            for i in range(n_parties)
        ]

    def _parse_trial_court(self) -> TexasTrialCourt:
        """
        Extracts the trial court info from the HTML tree. Will fail if
        `_parse_text` has not yet been called.

        :return: Trial court info.
        """
        info_panel: HtmlElement = self.tree.find(
            './/*[@id="panelTrialCourtInfo"]/div[2]'
        )
        fields: dict[str, str] = {
            clean_string(child.find(".//*[1]").text_content()): clean_string(
                child.find(".//*[2]").text_content()
            )
            for child in info_panel.iterchildren()
        }

        return TexasTrialCourt(
            name=fields.get("Court", ""),
            county=fields.get("County", ""),
            judge=fields.get("Court Judge", ""),
            case=fields.get("Court Case", ""),
            reporter=fields.get("Reporter", ""),
            punishment=fields.get("Punishment", ""),
        )

    @staticmethod
    def _parse_case_documents(cell: HtmlElement) -> list[TexasCaseDocument]:
        """
        Helper method to parse case documents for a given docket entry.

        Tries to find a table in the given cell and extracts the document URLs
        and names from it. If no table is found, returns an empty list.

        :param cell: The parent element containing the case documents.

        :return: List of case documents.
        """
        table = cell.find(".//table")
        if table is None:
            return []
        documents = parse_table(table)
        anchors = [parent.find(".//a") for parent in documents["0"]]
        urls: list[str] = [anchor.get("href") for anchor in anchors]
        query_dicts: list[dict[str, list[str]]] = [
            parse_qs(urlparse(url).query) for url in urls
        ]
        media_ids = [
            (query.get("MediaID", []), query.get("MediaVersionID", []))
            for query in query_dicts
        ]
        descriptions: list[str] = [
            clean_string(document.text_content())
            for document in documents["1"]
        ]
        file_size_matches = [
            FILE_SIZE_RE.search(anchor.text_content()) for anchor in anchors
        ]
        file_size_strs = [
            match.group(0) if match is not None else ""
            for match in (file_size_matches)
        ]

        return [
            TexasCaseDocument(
                document_url=url,
                description=description,
                media_id=media_id[0] if len(media_id) > 0 else "",
                media_version_id=media_version_id[0]
                if len(media_version_id) > 0
                else "",
                file_size_str=file_size_str,
                file_size_bytes=size_string_to_bytes(file_size_str),
            )
            for url, (
                media_id,
                media_version_id,
            ), description, file_size_str in zip(
                urls, media_ids, descriptions, file_size_strs
            )
        ]

    def _parse_case_events(self) -> list[TexasCaseEvent]:
        """
        Extracts and parses case events.

        This method processes the "Case Events" table and produces a list of
        TexasCaseEvent objects. If the table is empty, an empty list is
        returned.

        :return: A list of parsed TexasCaseEvent objects.
        """
        # Works because when there are no entries, Texas places a single <td>
        # element, which will be parsed by parse_table as 1 entry in the first
        # column and 0 in all others.
        if len(self.events["Event Type"]) == 0:
            return []
        n = len(self.events["Date"])

        return [
            TexasCaseEvent(
                date=datetime.strptime(
                    clean_string(self.events["Date"][i].text_content()),
                    self.date_format,
                ).date(),
                type=clean_string(self.events["Event Type"][i].text_content()),
                attachments=self._parse_case_documents(
                    self.events["Document"][i]
                ),
                disposition=clean_string(
                    self.events["Disposition"][i].text_content()
                ),
            )
            for i in range(n)
        ]

    def _parse_appellate_briefs(self) -> list[TexasAppellateBrief]:
        """
        Extracts and parses appellate briefs.

        This method processes the "Appellate Briefs" table and produces a list
        of TexasAppellateBrief objects. If the table is empty, an empty list is
        returned.

        :return: A list of parsed TexasAppellateBrief objects.
        """
        # Works because when there are no entries, Texas places a single <td>
        # element, which will be parsed by parse_table as 1 entry in the first
        # column and 0 in all others.
        if len(self.briefs["Event Type"]) == 0:
            return []
        n = len(self.briefs["Date"])

        return [
            TexasAppellateBrief(
                date=datetime.strptime(
                    clean_string(self.briefs["Date"][i].text_content()),
                    self.date_format,
                ).date(),
                type=clean_string(self.briefs["Event Type"][i].text_content()),
                attachments=self._parse_case_documents(
                    self.briefs["Document"][i]
                ),
                description=clean_string(
                    self.briefs["Description"][i].text_content()
                ),
            )
            for i in range(n)
        ]
