import email
from typing import Optional, TypedDict
from urllib.parse import parse_qs, urlparse

from lxml.html import HtmlElement

from juriscraper.abstract_parser import AbstractParser
from juriscraper.AbstractSite import logger
from juriscraper.lib.email_utils import parse_email_html
from juriscraper.state.texas.common import CourtID

COURT_NAME_TO_ID = {
    "first court of appeals": CourtID.FIRST_COURT_OF_APPEALS.value,
    "second court of appeals": CourtID.SECOND_COURT_OF_APPEALS.value,
    "third court of appeals": CourtID.THIRD_COURT_OF_APPEALS.value,
    "fourth court of appeals": CourtID.FOURTH_COURT_OF_APPEALS.value,
    "fifth court of appeals": CourtID.FIFTH_COURT_OF_APPEALS.value,
    "sixth court of appeals": CourtID.SIXTH_COURT_OF_APPEALS.value,
    "seventh court of appeals": CourtID.SEVENTH_COURT_OF_APPEALS.value,
    "eighth court of appeals": CourtID.EIGHTH_COURT_OF_APPEALS.value,
    "ninth court of appeals": CourtID.NINTH_COURT_OF_APPEALS.value,
    "tenth court of appeals": CourtID.TENTH_COURT_OF_APPEALS.value,
    "eleventh court of appeals": CourtID.ELEVENTH_COURT_OF_APPEALS.value,
    "twelfth court of appeals": CourtID.TWELFTH_COURT_OF_APPEALS.value,
    "thirteenth court of appeals": CourtID.THIRTEENTH_COURT_OF_APPEALS.value,
    "fourteenth court of appeals": CourtID.FOURTEENTH_COURT_OF_APPEALS.value,
    "fifteenth court of appeals": CourtID.FIFTEENTH_COURT_OF_APPEALS.value,
    "court of criminal appeals": CourtID.COURT_OF_CRIMINAL_APPEALS.value,
    "supreme court": CourtID.SUPREME_COURT.value,
}

SUBJECT_PREFIX = "Automated Case Update from "


class TamesEmailData(TypedDict):
    court_id: str
    case_number: str
    url: str


class TamesEmail(AbstractParser):
    """Parse TAMES case notification emails from Texas courts."""

    def __init__(self, court_id: str = "") -> None:
        self.court_id: str = court_id
        self.tree: Optional[HtmlElement] = None
        self.message: Optional[email.message.Message] = None
        self._court_id: Optional[str] = None

    @property
    def data(self) -> Optional[TamesEmailData]:
        if self._court_id is None or self.tree is None:
            raise ValueError("Unable to parse email")

        url = self._parse_case_url()
        if url is None:
            raise ValueError("No url found in email")

        case_number = parse_qs(urlparse(url).query).get("cn", [None])[0]
        if case_number is None:
            logger.error("Unable to extract case number from URL: %s", url)
            return None

        return TamesEmailData(
            court_id=self._court_id,
            url=url,
            case_number=case_number,
        )

    def _parse_text(self, text: str) -> None:
        self.message = email.message_from_string(text)
        subject = self.message.get("Subject", failobj="")

        if not subject.startswith(SUBJECT_PREFIX):
            logger.error(
                "Email subject did not match expected prefix. Subject: %s",
                subject,
            )
            return

        court_name = subject.removeprefix(SUBJECT_PREFIX).lower()
        self._court_id = COURT_NAME_TO_ID.get(court_name)
        if self._court_id is None:
            logger.error("Unknown court name in subject: %s", court_name)
            return

        self.tree = parse_email_html(text)

    def _parse_case_url(self) -> Optional[str]:
        anchor = self.tree.find(".//a")
        if anchor is None:
            logger.error("Unable to find link in email body")
            return None
        return anchor.get("href")
