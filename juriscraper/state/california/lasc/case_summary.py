"""Parsers for the Los Angeles Superior Court's free case summary.

The case summary search at `CASE_SUMMARY_SEARCH_URL` takes one case number at
a time. Posting a number the court knows redirects to `CASE_SUMMARY_URL`,
which shows that case to the same session; posting one it doesn't know
returns the search page with a message instead (see
`search_refusal`). It covers civil, small claims, family law and
probate cases.

Both pages must be requested on the ``www`` host: the bare
``lacourt.ca.gov`` host answers the search post with an error page.
"""

import re
from collections import defaultdict
from datetime import date, datetime
from enum import Enum

from lxml import html as lxml_html
from lxml.html import HtmlElement
from pydantic import BaseModel
from typing_extensions import override

from juriscraper.abstract_parser import LegacyParser, ParserValidationError
from juriscraper.lib.string_utils import CaseNameTweaker, harmonize
from juriscraper.state.docket import (
    Docket,
    DocketEntry,
    DocketEntryType,
    DocketTransfer,
    DocketType,
    Document,
    Party,
    PartyType,
    Representative,
)

CASE_SUMMARY_SEARCH_URL = (
    "https://www.lacourt.ca.gov/casesummary/v2web3/?casetype=civil"
)
CASE_SUMMARY_URL = "https://www.lacourt.ca.gov/casesummary/v2web3/CaseSummary"

# The anchor naming each section. Every section's rows follow its anchor in a
# `dataTable`; a section with nothing to show may have no table at all.
CASE_INFORMATION = "CaseInformation"
FUTURE_HEARINGS = "FutureHearings"
PARTIES = "Parties"
DOCUMENTS_FILED = "DocumentsFiled"
PAST_PROCEEDINGS = "PastProceedings"
REGISTER_OF_ACTIONS = "RegisterOfAction"
SECTIONS = frozenset(
    {
        CASE_INFORMATION,
        FUTURE_HEARINGS,
        PARTIES,
        DOCUMENTS_FILED,
        PAST_PROCEEDINGS,
        REGISTER_OF_ACTIONS,
    }
)

# The notice the case summary shows in place of a restricted case, such as a
# confidential unlawful detainer, which only its parties may view.
RESTRICTED_CASE_MARKER = "not authorized to view this case"
RESTRICTED_CASE_RE = re.compile(r"Case Number \S+ is a confidential [^.]*\.")

ATTORNEY_ROLE_RE = re.compile(r"^Attorney for (?P<role>.+)$", re.IGNORECASE)
FILED_BY_RE = re.compile(
    r"^Filed by\s+(?P<name>.*?)(?:\s*\((?P<role>[^()]+)\))?$", re.IGNORECASE
)
DEPARTMENT_RE = re.compile(r"^Department\s+", re.IGNORECASE)

# Checked in order against a document's type, so the more specific kinds of
# filing come first: a "Notice of Motion" is a motion.
ENTRY_TYPE_KEYWORDS: tuple[tuple[str, DocketEntryType], ...] = (
    ("motion", DocketEntryType.MOTION),
    ("judgment", DocketEntryType.DISPOSITION),
    ("dismissal", DocketEntryType.DISPOSITION),
    ("order", DocketEntryType.ORDER),
    ("petition", DocketEntryType.PETITION),
    ("complaint", DocketEntryType.PETITION),
    ("brief", DocketEntryType.BRIEF),
    ("letter", DocketEntryType.LETTER),
    ("notice", DocketEntryType.NOTICE),
)

cnt = CaseNameTweaker()


class LASCRepresentative(Representative):
    """An attorney of record for a party."""


class LASCParty(Party[LASCRepresentative]):
    """A party to a case.

    :ivar role: The party's role as the court printed it, e.g. ``Defendant``.
        Trial court roles have no equivalent in `PartyType`, so `party_type`
        is always ``UNKNOWN``.
    """

    role: str


class LASCAttorney(BaseModel):
    """An attorney the case summary lists.

    The court names only the role an attorney appears for, not the party, so
    an attorney is only added to a party's representatives when exactly one
    party has that role.

    :ivar name: The attorney's name as printed.
    :ivar represents: The role the attorney appears for, e.g. ``Plaintiff``.
    """

    name: str
    represents: str


class LASCDocketEntry(DocketEntry[Document]):
    """A document filed in a case.

    The court doesn't publish documents for free, so `attachments` is always
    empty.

    :ivar document_type: The kind of document, e.g. ``Minute Order``.
    :ivar description: The court's further description of the document, if
        any.
    :ivar filed_by: Who filed the document, e.g. ``Clerk``.
    :ivar filed_by_role: The filer's role in the case, when the filer is a
        party.
    """

    document_type: str
    description: str
    filed_by: str
    filed_by_role: str | None


class LASCHearing(BaseModel):
    """A hearing, either scheduled or already held.

    :ivar hearing_date: The date of the hearing.
    :ivar time: The time of the hearing as printed.
    :ivar department: The department hearing it, e.g. ``514``.
    :ivar event: The kind of hearing, e.g. ``Jury Trial``.
    :ivar address: The courthouse address. Only printed for future hearings.
    :ivar result: What came of the hearing, e.g. ``Held``. Empty for future
        hearings.
    :ivar upcoming: Whether the hearing was listed as a future hearing.
    """

    hearing_date: date
    time: str
    department: str
    event: str
    address: str
    result: str
    upcoming: bool


class LASCAction(BaseModel):
    """An entry in the case's register of actions.

    :ivar date_of_action: The date of the action.
    :ivar text: The action as the court described it.
    """

    date_of_action: date
    text: str


class LASCCaseSummary(Docket[DocketTransfer, LASCDocketEntry, LASCParty]):
    """A case as the free case summary shows it.

    :ivar courthouse: The courthouse the case was filed in.
    :ivar case_type: The case type as printed, e.g. ``Premise Liability (...)
        (General Jurisdiction)``.
    :ivar status: The case's status, e.g. ``Pending``.
    :ivar attorneys: Every attorney listed, including those that couldn't be
        matched to a party.
    :ivar hearings: Future hearings, then past proceedings.
    :ivar actions: The register of actions, newest first.
    """

    courthouse: str
    case_type: str
    status: str
    attorneys: list[LASCAttorney]
    hearings: list[LASCHearing]
    actions: list[LASCAction]


def _text(element: HtmlElement) -> str:
    """The element's text on one line.

    :param element: The element.
    :return: Its text with whitespace collapsed.
    """
    return " ".join(element.text_content().split())


def _parse_date(value: str) -> date:
    """Parse a date the case summary prints, e.g. ``7/9/2025``.

    :param value: The date as printed.
    :return: The date.
    """
    return datetime.strptime(value.strip(), "%m/%d/%Y").date()


def _department(value: str) -> str:
    """Reduce ``Department  514`` to ``514``.

    :param value: The department as printed.
    :return: The department's name alone.
    """
    return DEPARTMENT_RE.sub("", " ".join(value.split()))


def _entry_type(document_type: str) -> DocketEntryType:
    """Classify a filed document by its type.

    :param document_type: The document's type, e.g. ``Notice of Ruling``.
    :return: The first matching entry type, or ``UNKNOWN``.
    """
    lowered = document_type.lower()
    for keyword, entry_type in ENTRY_TYPE_KEYWORDS:
        if keyword in lowered:
            return entry_type
    return DocketEntryType.UNKNOWN


def _section_rows(tree: HtmlElement) -> dict[str, list[list[HtmlElement]]]:
    """Find each section's rows.

    Walks the page in document order, so a section with no table doesn't
    borrow the next section's rows.

    :param tree: The parsed page.
    :return: Each section's rows, as lists of cells, keyed by anchor name.
    """
    rows: dict[str, list[list[HtmlElement]]] = {}
    current: str | None = None
    for element in tree.iter("a", "table"):
        if element.tag == "a":
            if (name := element.get("name")) in SECTIONS:
                current = name
            continue
        classes = (element.get("class") or "").split()
        if current is None or current in rows or "dataTable" not in classes:
            continue
        rows[current] = [
            row.xpath("./td") for row in element.xpath("./tr|./tbody/tr")
        ]
    return rows


def build_case_search_form_data(
    search_page_html: str, case_number: str
) -> dict[str, str]:
    """Build the form data that looks up one case.

    :param search_page_html: The search page, fetched in the same session the
        form data will be posted from; it carries the form's anti-forgery
        token.
    :param case_number: The case number to look up.
    :return: The form fields to post to `CASE_SUMMARY_SEARCH_URL`.
    :raises ValueError: If the page has no case summary form.
    """
    tree = lxml_html.fromstring(search_page_html)
    tokens = tree.xpath(
        "//form[@id='caseSummaryForm']"
        "//input[@name='__RequestVerificationToken']/@value"
    )
    if not tokens:
        raise ValueError("The search page has no case summary form.")
    return {
        "txtCaseNumber": case_number,
        "ddlCourthouse": "",
        "action": "Search",
        "__RequestVerificationToken": tokens[0],
    }


def _messages(tree: HtmlElement) -> list[str]:
    """Read the court's messages from a page.

    :param tree: The parsed page.
    :return: The text of each non-empty message element, in page order.
    """
    messages = tree.xpath(
        "//div[contains(concat(' ', normalize-space(@class), ' '), "
        "' message ')]"
    )
    return [text for message in messages if (text := _text(message))]


class Refusal(Enum):
    """Why a search gave back something other than a case summary."""

    NOT_FOUND = "not found"
    """The court has no case with that number, or won't answer for it."""
    RESTRICTED = "restricted"
    """The case may only be viewed by its parties."""


def search_refusal(page_html: str) -> tuple[Refusal, str] | None:
    """Recognize a page the search gave back in place of a case summary.

    A number the court knows redirects to the summary. One it doesn't comes
    back as the search page with a message; a case only its parties may view
    — a confidential unlawful detainer, say, which needs a court-issued
    access code even though its number's litigation type is civil — comes
    back as a notice and an access form. A restricted case carries a message
    of its own, so it is recognized first.

    :param page_html: The page the search post ended at.
    :return: Why the court refused and what it said about it, e.g.
        ``(Refusal.NOT_FOUND, "No match found for case number
        25STCV99998.")``. `None` when the page is a case summary.
    """
    tree = lxml_html.fromstring(page_html)
    messages = _messages(tree)
    notices = [
        message
        for message in messages
        if RESTRICTED_CASE_MARKER in message.lower()
    ]
    if notices:
        explanation = RESTRICTED_CASE_RE.search(_text(tree))
        return Refusal.RESTRICTED, (
            explanation.group(0) if explanation else notices[0]
        )
    return (Refusal.NOT_FOUND, messages[0]) if messages else None


class CaseSummaryParser(LegacyParser[LASCCaseSummary]):
    """Parse a case summary page."""

    @override
    def _parse(self, i: str) -> LASCCaseSummary:
        """Parse the case summary.

        :param i: The case summary page.
        :return: The case.
        :raises ParserValidationError: If the page has no case number,
            title or filing date, which means it isn't a case summary or
            its markup changed.
        """
        tree = lxml_html.fromstring(i)
        sections = _section_rows(tree)

        info = {
            _text(cells[0]).rstrip(":").strip().lower(): _text(cells[1])
            for cells in sections.get(CASE_INFORMATION, [])
            if len(cells) >= 2
        }
        case_number = info.get("case information", "").upper()
        title = info.get("case title", "")
        filed = info.get("filing date", "")
        if not (case_number and title and filed):
            raise ParserValidationError(
                "The page has no case number, title or filing date."
            )

        case_name = harmonize(title)
        parties, attorneys = self._parties(sections.get(PARTIES, []))
        return LASCCaseSummary(
            court_id=self.court_id,
            docket_number=case_number,
            case_name=case_name,
            case_name_full=title,
            case_name_short=cnt.make_case_name_short(case_name),
            date_filed=_parse_date(filed),
            transfers=[],
            entries=self._entries(sections.get(DOCUMENTS_FILED, [])),
            parties=parties,
            docket_type=DocketType.CIVIL,
            courthouse=info.get("filing courthouse", ""),
            case_type=info.get("case type", ""),
            status=info.get("status", ""),
            attorneys=attorneys,
            hearings=self._hearings(
                sections.get(FUTURE_HEARINGS, []),
                sections.get(PAST_PROCEEDINGS, []),
            ),
            actions=[
                LASCAction(
                    date_of_action=_parse_date(_text(cells[0])),
                    text=_text(cells[1]),
                )
                for cells in sections.get(REGISTER_OF_ACTIONS, [])
                if len(cells) >= 2
            ],
        )

    @staticmethod
    def _parties(
        rows: list[list[HtmlElement]],
    ) -> tuple[list[LASCParty], list[LASCAttorney]]:
        """Split the party rows into parties and attorneys.

        :param rows: The party section's rows.
        :return: The parties, with each attorney that could be matched to a
            single party among its representatives, and every attorney.
        """
        by_role: defaultdict[str, list[LASCParty]] = defaultdict(list)
        parties: list[LASCParty] = []
        attorneys: list[LASCAttorney] = []
        for cells in rows:
            if len(cells) < 2:
                continue
            name, role = _text(cells[0]), _text(cells[1])
            if match := ATTORNEY_ROLE_RE.match(role):
                attorneys.append(
                    LASCAttorney(name=name, represents=match["role"])
                )
                continue
            party = LASCParty(
                name=name,
                party_type=PartyType.UNKNOWN,
                representatives=[],
                role=role,
            )
            parties.append(party)
            by_role[role.lower()].append(party)
        for attorney in attorneys:
            candidates = by_role[attorney.represents.lower()]
            if len(candidates) == 1:
                candidates[0].representatives.append(
                    LASCRepresentative(name=attorney.name)
                )
        return parties, attorneys

    @staticmethod
    def _entries(rows: list[list[HtmlElement]]) -> list[LASCDocketEntry]:
        """Parse the documents filed.

        :param rows: The documents filed section's rows.
        :return: The documents, newest first, as the court lists them.
        """
        entries: list[LASCDocketEntry] = []
        for cells in rows:
            if len(cells) < 3:
                continue
            lines = [
                " ".join(line.split())
                for line in cells[1].text_content().splitlines()
            ]
            lines = [line for line in lines if line]
            document_type = lines[0] if lines else ""
            description = " ".join(lines[1:])
            if description.startswith("(") and description.endswith(")"):
                description = description[1:-1].strip()
            filed_by, filed_by_role = _text(cells[2]), None
            if match := FILED_BY_RE.match(filed_by):
                filed_by, filed_by_role = match["name"], match["role"]
            entries.append(
                LASCDocketEntry(
                    date_filed=_parse_date(_text(cells[0])),
                    attachments=[],
                    entry_type=_entry_type(document_type),
                    document_type=document_type,
                    description=description,
                    filed_by=filed_by,
                    filed_by_role=filed_by_role,
                )
            )
        return entries

    @staticmethod
    def _hearings(
        future_rows: list[list[HtmlElement]],
        past_rows: list[list[HtmlElement]],
    ) -> list[LASCHearing]:
        """Parse the future hearings and past proceedings.

        :param future_rows: The future hearings section's rows: date, time,
            department, address and event.
        :param past_rows: The past proceedings section's rows: date and time,
            department, event and result.
        :return: The future hearings, then the past proceedings.
        """
        hearings = [
            LASCHearing(
                hearing_date=_parse_date(_text(cells[0])),
                time=_text(cells[1]),
                department=_department(_text(cells[2])),
                address=_text(cells[3]),
                event=_text(cells[4]),
                result="",
                upcoming=True,
            )
            for cells in future_rows
            if len(cells) >= 5
        ]
        for cells in past_rows:
            if len(cells) < 4:
                continue
            day, _, time = _text(cells[0]).partition(" ")
            hearings.append(
                LASCHearing(
                    hearing_date=_parse_date(day),
                    time=time,
                    department=_department(_text(cells[1])),
                    address="",
                    event=_text(cells[2]),
                    result=_text(cells[3]),
                    upcoming=False,
                )
            )
        return hearings
