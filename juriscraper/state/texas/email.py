import email
from typing import Optional, TypedDict
from urllib.parse import parse_qs, urlparse

from lxml.html import HtmlElement

from juriscraper.AbstractSite import logger
from juriscraper.lib.email_utils import parse_email_html
from juriscraper.state.texas.common import CourtID

COURT_NAME_TO_ID = {
    "First Court of Appeals": CourtID.FIRST_COURT_OF_APPEALS.value,
    "Second Court of Appeals": CourtID.SECOND_COURT_OF_APPEALS.value,
    "Third Court of Appeals": CourtID.THIRD_COURT_OF_APPEALS.value,
    "Fourth Court of Appeals": CourtID.FOURTH_COURT_OF_APPEALS.value,
    "Fifth Court of Appeals": CourtID.FIFTH_COURT_OF_APPEALS.value,
    "Sixth Court of Appeals": CourtID.SIXTH_COURT_OF_APPEALS.value,
    "Seventh Court of Appeals": CourtID.SEVENTH_COURT_OF_APPEALS.value,
    "Eighth Court of Appeals": CourtID.EIGHTH_COURT_OF_APPEALS.value,
    "Ninth Court of Appeals": CourtID.NINTH_COURT_OF_APPEALS.value,
    "Tenth Court of Appeals": CourtID.TENTH_COURT_OF_APPEALS.value,
    "Eleventh Court of Appeals": CourtID.ELEVENTH_COURT_OF_APPEALS.value,
    "Twelfth Court of Appeals": CourtID.TWELFTH_COURT_OF_APPEALS.value,
    "Thirteenth Court of Appeals": CourtID.THIRTEENTH_COURT_OF_APPEALS.value,
    "Fourteenth Court of Appeals": CourtID.FOURTEENTH_COURT_OF_APPEALS.value,
    "Fifteenth Court of Appeals": CourtID.FIFTEENTH_COURT_OF_APPEALS.value,
    "Court of Criminal Appeals": CourtID.COURT_OF_CRIMINAL_APPEALS.value,
    "Supreme Court": CourtID.SUPREME_COURT.value,
}

SUBJECT_PREFIX = "Automated Case Update from "


class TamesEmailData(TypedDict):
    court_id: str
    case_number: str
    url: str


class TamesEmail:
    """Parse TAMES case notification emails from Texas courts."""

    def __init__(self, court_id: str = "") -> None:
        self.court_id: str = court_id
        self.tree: Optional[HtmlElement] = None
        self.message: Optional[email.message.Message] = None
        self._court_id: Optional[str] = None

    @property
    def data(self) -> Optional[TamesEmailData]:
        if self._court_id is None or self.tree is None:
            return None

        url = self._parse_case_url()
        if url is None:
            return None

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

        court_name = subject[len(SUBJECT_PREFIX) :]
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
