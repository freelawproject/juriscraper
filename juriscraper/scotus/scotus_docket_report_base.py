from abc import ABC, abstractmethod
from datetime import date
from typing import Any, TypedDict, final

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


class SCOTUSDocketReportBase(ABC):
    """Parse SCOTUS docket"""

    @property
    @final
    def data(self) -> dict[str, Any]:
        """Get all the data back from this endpoint."""
        metadata = self.metadata or {}
        if not metadata:
            return {}
        case_name = metadata.get("case_name")
        if not case_name:
            logger.error("Failed to extract SCOTUS case name.")
            return {}
        docket_number = metadata.get("docket_number")
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
    def metadata(self) -> dict[str, Any]: ...

    @property
    @abstractmethod
    def parties(self) -> list[Party]: ...

    @property
    @abstractmethod
    def docket_entries(self) -> list[DocketEntry]: ...
