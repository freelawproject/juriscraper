import re
from urllib.parse import parse_qs, urlparse

from juriscraper.state.texas.common import CourtID


def get_tames_court_from_subject(subject: str, default=None):
    if not subject.startswith("Automated Case Update from"):
        return default
    return {
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
    }.get(subject[27:], default)


link_href = re.compile('<a href="([^"]*)">')


def get_tames_case_from_email_body(body: str, default=None):
    match = re.search(link_href, body)
    if not match:
        return default
    link = match.group(1)
    if not link:
        return default
    case_number = parse_qs(urlparse(link).query)["cn"][0]
    return {"url": link, "case_number": case_number}
