"""Normalized records shared by the SCOTUS JSON and HTML docket parsers."""

from datetime import date

from typing_extensions import TypedDict


class _SCOTUSMetadata(TypedDict, total=False):
    docket_number: str | None
    capital_case: bool | None
    date_filed: date | None
    case_name: str
    links: str
    lower_court: str | None
    lower_court_case_numbers_raw: str | None
    lower_court_case_numbers: list[str] | None
    lower_court_decision_date: date | None
    lower_court_rehearing_denied_date: date | None
    questions_presented: str | None
    discretionary_court_decision: date | None


class SCOTUSMetadata(_SCOTUSMetadata, closed=True):
    pass


class SCOTUSAttachment(TypedDict):
    description: str
    document_url: str | None
    document_number: int | None


class SCOTUSDocketEntry(TypedDict):
    date_filed: date | None
    document_number: int | None
    description: str
    description_html: str
    attachments: list[SCOTUSAttachment]


class SCOTUSAttorney(TypedDict):
    name: str | None
    is_counsel_of_record: bool
    title: str | None
    phone: str | None
    address: str | None
    city: str | None
    state: str | None
    zip: str | None
    email: str | None


class SCOTUSParty(TypedDict):
    type: str
    name: str
    attorneys: list[SCOTUSAttorney]


class SCOTUSDocket(_SCOTUSMetadata, total=False, closed=True):
    parties: list[SCOTUSParty]
    docket_entries: list[SCOTUSDocketEntry]
