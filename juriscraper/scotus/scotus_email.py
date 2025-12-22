import email
import pprint
import re
import sys
from datetime import datetime
from email.message import EmailMessage
from enum import Enum
from pathlib import Path
from typing import Optional, TypedDict, Union
from urllib.parse import parse_qs, urlparse

import requests
from lxml import html
from lxml.html import HtmlElement

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import clean_html
from juriscraper.lib.string_utils import clean_string, harmonize
from juriscraper.scotus import SCOTUSDocketReportHTML


class SCOTUSEmailType(Enum):
    """
    Enum for the different types of emails that can be received from SCOTUS.
    """

    INVALID = "invalid"
    CONFIRMATION = "confirmation"
    DOCKET_ENTRY = "docket_entry"


class SCOTUSNotificationEmail(TypedDict):
    """
    Schema for data extracted from SCOTUS notification emails.

    :ivar docket_number: The docket number of the case from the email.
    :ivar case_name: The name of the case from the email.
    :ivar entry_description: The description of the docket entry from the
    email.
    """

    docket_number: str
    case_name: str
    entry_description: str


class SCOTUSEmailData(TypedDict):
    """
    Schema for data extracted from SCOTUS emails.

    :ivar email_type: The type of email this data is extracted from.
    :ivar followup_url: The URL to perform the next action in the email flow
    (confirmation link for confirmation emails, case URL for docket entry
    emails). Must be set if the email type is valid and must be an empty string
    otherwise.
    :ivar email_datetime: The time (extracted from the "Date" email header) the
    email was sent.
    :ivar data: The data extracted from the email. Type corresponds to
    `email_type` (DOCKET_ENTRY: SCOTUSNotificationEmail; CONFIRMATION,
    UNKNOWN: None).
    """

    email_type: str
    followup_url: str
    email_datetime: datetime
    data: Optional[SCOTUSNotificationEmail]


class SCOTUSEmailHandlingResult(TypedDict):
    """
    Schema for result of handling SCOTUS emails.
    """

    email_type: str
    data: Union[dict[str, str], str]


class SCOTUSConfirmationResult(Enum):
    """
    Enum for the possible results of attempting to confirm a subscription to
    SCOTUS emails.
    """

    BadRequest = "bad_request"
    """Possibly: the request was malformed or missing required parameters.
    Unclear from SCOTUS website."""
    Failed = "failed"
    """Possibly: The confirmation request failed for some reason. Unclear from
    SCOTUS website."""
    NoVerify = "no_verify"
    """Unclear from SCOTUS website."""
    LinkExpired = "link_expired"
    """The confirmation link has expired."""
    NotFound = "not_found"
    """The email address associated with the confirmation link was not found
    (don't ask me how that could happen)."""
    AlreadySubscribed = "duplicate"
    """The email address is already subscribed to SCOTUS emails."""
    Success = "success"
    """The subscription confirmation was successful."""
    Unknown = "unknown"
    """Unknown error. Used when we can't determine the confirmation result.
    Should never appear in practice and exists only for future-proofing."""


class _SCOTUSConfirmationPageScraper:
    """
    Special-purpose scraper for parsing the subscription confirmation page for
    SCOTUS email updates.

    Should only be used by `SCOTUSEmail`.

    Mainly exists to make testing easier.

    :ivar court_id: Court ID for the scraper.
    :ivar tree: Parsed HTML tree.
    """

    def __init__(self, court_id: str = "scotus"):
        self.court_id = court_id
        self.tree: Optional[HtmlElement] = None

    @property
    def data(self) -> str:
        """
        Determine the result of our attempt to confirm our subscription.

        :return: Result of the confirmation attempt.
        """
        body_content = self.tree.find(".//div[@class='body-content']")
        script_tag = body_content.find(".//script")
        script = script_tag.text_content()
        # The confirmation page by default displays all response messages
        # and uses a (presumably) server-generated if/else chain with
        # conditions set to `true` or `false` to determine which message to
        # display. A better solution would be to either render the page with
        # JS enabled or to parse the script tag into an AST, but this works
        # for now.
        match = re.search(r"true\)\s\{([^}]+)", script)
        if match is None:
            return SCOTUSConfirmationResult.NoVerify.value
        statement_body = match.group(1)
        visibility_calls = [
            line.strip() for line in statement_body.split("\n")[1:-1]
        ]
        visibility_re = re.compile(r"^\$\(\'#(.+)\'\)\.(show|hide)\(\);$")
        visibility_matches = [
            visibility_re.match(call) for call in visibility_calls
        ]
        confirmation_status = next(
            visibility_match.group(1)[3:].lower()
            for visibility_match in visibility_matches
            if visibility_match is not None
            and visibility_match.group(2) == "show"
        )

        if confirmation_status == "badrequest":
            return SCOTUSConfirmationResult.BadRequest.value
        if confirmation_status == "fail":
            return SCOTUSConfirmationResult.Failed.value
        if confirmation_status == "noverifymessage":
            return SCOTUSConfirmationResult.NoVerify.value
        if confirmation_status == "linkexpired":
            return SCOTUSConfirmationResult.LinkExpired.value
        if confirmation_status == "notfound":
            return SCOTUSConfirmationResult.NotFound.value
        if confirmation_status == "duplicate":
            return SCOTUSConfirmationResult.AlreadySubscribed.value
        if confirmation_status == "ok":
            return SCOTUSConfirmationResult.Success.value
        return SCOTUSConfirmationResult.Unknown.value

    def _parse_text(self, text: str) -> None:
        """Parse raw HTML and store a lxml tree."""
        self.tree = html.fromstring(clean_html(text))


class SCOTUSEmail:
    """Parse SCOTUS docket notification email."""

    TITLE_REGEX = re.compile(r"^A new docket entry, \"(.+?)\" has been added")
    DOCKET_ENTRY_SUBJECT_REGEX = re.compile(
        r"^Supreme Court Electronic Filing System$"
    )
    CONFIRMATION_SUBJECT_REGEX = re.compile(
        r"^Supreme Court Case Notification .+$"
    )

    def __init__(self, court_id: str = "scotus"):
        self.court_id: str = court_id
        self.tree: Optional[HtmlElement] = None
        self.message: Optional[EmailMessage] = None
        self.email_type: SCOTUSEmailType = SCOTUSEmailType.INVALID

    @property
    def data(self) -> SCOTUSEmailData:
        """Extract all the data in the email.

        If the email is a docket update email, the output will be formatted:

        :return: Data extracted from the email. The `data` key will be
        `None` if the email type is unknown or parsing fails.
        """

        if self.email_type == SCOTUSEmailType.DOCKET_ENTRY:
            followup_url = self._parse_first_link()
            data = SCOTUSNotificationEmail(
                docket_number=self._parse_docket_number(),
                case_name=self._parse_case_name(),
                entry_description=self._parse_filing_name(),
            )
        elif self.email_type == SCOTUSEmailType.CONFIRMATION:
            followup_url = self._parse_first_link()
            data = None
        else:
            followup_url = ""
            data = None

        return SCOTUSEmailData(
            email_type=self.email_type.value,
            followup_url=followup_url,
            email_datetime=self._parse_datetime(),
            data=data,
        )

    def handle_email(self, timeout: float = 10.0) -> SCOTUSEmailHandlingResult:
        """
        Handle next steps in email processing.

        If the email is a docket update, request the docket page and return the
        parsed data.

        If the email is a confirmation email, attempt to confirm the
        subscription and return the parsed result.

        :param timeout: Timeout for the HTTP request in seconds.

        :return: Result of handling the email.
        """
        if self.email_type == SCOTUSEmailType.INVALID:
            raise TypeError("Unknown email type.")

        # The `followup_url` property is guaranteed to be present if the
        # email type is valid.
        response = requests.get(
            self.data["followup_url"],
            headers={"User-Agent": "Free Law Project"},
            timeout=timeout,
        )
        response.raise_for_status()

        if self.email_type == SCOTUSEmailType.DOCKET_ENTRY:
            scotus_docket_report_html = SCOTUSDocketReportHTML(self.court_id)
            scotus_docket_report_html._parse_text(response.text)
            return SCOTUSEmailHandlingResult(
                email_type=self.email_type.value,
                data=scotus_docket_report_html.data,
            )

        # The only remaining possibility is a confirmation email.
        scotus_confirmation_page_scraper = _SCOTUSConfirmationPageScraper(
            self.court_id
        )
        scotus_confirmation_page_scraper._parse_text(response.text)
        return SCOTUSEmailHandlingResult(
            email_type=self.email_type.value,
            data=scotus_confirmation_page_scraper.data,
        )

    def _determine_email_type(self) -> SCOTUSEmailType:
        """Determine the type of the email (docket update/confirmation) based
        on the subject line. If the subject line does not match any known
        patterns, return `EmailType.INVALID`."""
        subject = self.message.get("Subject", failobj="")

        if self.DOCKET_ENTRY_SUBJECT_REGEX.match(subject) is not None:
            return SCOTUSEmailType.DOCKET_ENTRY
        elif self.CONFIRMATION_SUBJECT_REGEX.match(subject) is not None:
            return SCOTUSEmailType.CONFIRMATION
        logger.error(
            "Email subject did not match known patterns. Subject: %s", subject
        )
        return SCOTUSEmailType.INVALID

    def _parse_text(self, text: str) -> None:
        """Extract and store the first part of the email with the
        "Content-Type" header set to "text/html" and store a parsed HTML
        tree. Assumes that there will always be an email part with this
        content type. If lxml parsing fails, return `None` and log an
        appropriate error.

        :param text: The raw email text.

        :return: None
        """
        self.message = email.message_from_string(text)
        email_type = self._determine_email_type()

        if email_type == SCOTUSEmailType.INVALID:
            return

        content_part = next(
            (
                part
                for part in self.message.walk()
                if part.get_content_type() == "text/html"
                and not part.is_multipart()
            ),
            None,
        )

        if content_part is None:
            logger.error(
                "Unable to find non-multipart content part with 'text/html' "
                "content type in email"
            )
            return

        payload = content_part.get_payload(decode=True)
        charset = content_part.get_content_charset(content_part.get_charset())

        try:
            body = payload.decode(charset)
        except UnicodeDecodeError:
            logger.error(
                "Unable to decode email payload with charset '%s'", charset
            )
            return

        self.tree = html.fromstring(clean_html(body))

        n_anchors = sum(1 for _ in self.tree.iterfind(".//a"))

        if email_type == SCOTUSEmailType.DOCKET_ENTRY:
            if self.message.get("Date") is None:
                logger.error("Unable to find 'Date' header in email")
                return

            if n_anchors < 2:
                logger.error(
                    "Unable to find at least two links in email body (should "
                    "be case link and unsubscribe link); found %d",
                    n_anchors,
                )
                return

            text = self.tree.text_content()
            if self.TITLE_REGEX.match(text) is None:
                logger.error(
                    "Unable to find match for docket entry title regex in "
                    "email"
                )
                return

            self.email_type = email_type
        elif email_type == SCOTUSEmailType.CONFIRMATION:
            if n_anchors != 1:
                logger.error(
                    "Incorrect number of links in email body. Should be "
                    "exactly one (confirmation link); found %d",
                    n_anchors,
                )
                return
            self.email_type = email_type

    def _parse_datetime(self) -> Optional[datetime]:
        """Extract the "Date" header in the notification email message into a
        `datetime`, returning `None` if the header is absent or parsing fails
        and logging an appropriate error.

        :return: `datetime` or `None` if unable to parse the "Date" header.
        """
        message_date = self.message.get("Date")

        try:
            return datetime.strptime(message_date, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            logger.error(
                "Unable to parse 'Date' header of email (value is '%s')",
                message_date,
            )
            return None

    def _parse_filing_name(self) -> str:
        """Extract the docket entry title from the email body using a regex
        and clean it with the `clean_string` method. Return `None` and log
        an error if the regex fails to match the email.

        :return: Clean docket entry title.
        """
        text = self.tree.text_content()
        match = self.TITLE_REGEX.match(text)

        return clean_string(match.group(1))

    def _parse_case_name(self) -> str:
        """Extract the case name from the first `<a>` tag in the email body
        and uses the `harmonize` method to clean it.

        :return: Cleaned case name.
        """
        return harmonize(self.tree.findtext(".//a"))

    def _parse_docket_number(self) -> str:
        """Extract the docket number using the `href` attribute from the first
        `<a>` tag in the email body.

        :return: Docket number.
        """
        file = parse_qs(urlparse(self.tree.find(".//a").get("href")).query)[
            "filename"
        ][0]
        docket_number = Path(file).stem
        return clean_string(docket_number)

    def _parse_first_link(self) -> str:
        """Extract the `href` attribute from the first `<a>` tag in the email
        body.
        """
        return self.tree.find(".//a").get("href")


def _main():
    """Parse a local email file and pretty print extracted data.

    :return: None
    """
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.scotus_email <filepath>")
        print("Please provide a path to an email file to parse.")
        sys.exit(1)

    report = SCOTUSEmail()
    filepath = sys.argv[1]
    print(f"Parsing email file at {filepath}")
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
