from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Never, TypedDict, cast, final

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()


class Attorney(TypedDict):
    name: str | None
    is_counsel_of_record: bool
    phone: str | None
    title: str | None
    address: str | None
    city: str | None
    state: str | None
    zip: str | None
    email: str | None


class Party(TypedDict):
    type: str
    name: str
    attorneys: list[Attorney]


class Attachment(TypedDict):
    description: str
    document_url: str
    document_number: int | None


class DocketEntry(TypedDict):
    date_filed: date | None
    document_number: int | None
    description: str
    description_html: str
    attachments: list[Attachment] | None


class Metadata(TypedDict):
    docket_number: str | None
    capital_case: bool | None
    date_filed: date | None
    case_name: str | None
    links: str | None
    lower_court: str | None
    lower_court_case_numbers_raw: str | None
    lower_court_case_numbers: list[str] | None
    lower_court_decision_date: date | None
    lower_court_rehearing_denied_date: date | None
    questions_presented: str | None
    discretionary_court_decision: date | None


class SCOTUSDocketReportBase(ABC):
    """Parse SCOTUS docket"""

    @property
    @final
    def data(self) -> dict[str, Any]:
        """Get all the data back from this endpoint."""
        metadata = self.metadata
        if not metadata:
            return {}
        metadata = cast(Metadata, metadata)  # TODO[Pyrefly 1.4.0]: drop cast
        case_name = metadata["case_name"]
        if not case_name:
            logger.error("Failed to extract SCOTUS case name.")
            return {}
        docket_number = metadata["docket_number"]
        if not docket_number:
            logger.error("Failed to extract SCOTUS docket number.")
            return {}
        return {
            **metadata,
            "parties": self.parties,
            "docket_entries": self.docket_entries,
        }

    @abstractmethod
    def _parse_text(self, text: str) -> None: ...

    @property
    @abstractmethod
    def metadata(self) -> Metadata | dict[Never, Never]: ...

    @property
    @abstractmethod
    def parties(self) -> list[Party]: ...

    @property
    @abstractmethod
    def docket_entries(self) -> list[DocketEntry]: ...
