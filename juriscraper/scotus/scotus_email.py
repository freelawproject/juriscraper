import email
import pprint
import re
import sys
from datetime import datetime
from email.message import EmailMessage
from enum import Enum, auto
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

from lxml import html
from lxml.html import HtmlElement

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import clean_html
from juriscraper.lib.string_utils import clean_string, harmonize


class EmailType(Enum):
    INVALID = auto()
    CONFIRMATION = auto()
    DOCKET_ENTRY = auto()


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
        self.email_type: EmailType = EmailType.INVALID

    @property
    def data(self) -> dict:
        """Extract all the data in the email.

        If the email is a docket update email, the output will be formatted:

        {
            "email_type": "docket_entry",
            "docket_number": "25-250",
            "notification_datetime": "2025-10-09 02:04:05+00:00",
            "case_name": "Donald J. Trump, President of the United States v. V.O.S. Selections, Inc.",
            "case_url": "https://www.supremecourt.gov/search.aspx?filename=/docket/DocketFiles/html/Public/25-250.html",
            "entry_description": "Amicus brief of Corey J. Biazzo, Esq. submitted."
        }

        If the email is a confirmation email, the output will be formatted:

        {
            "email_type": "confirmation",
            "confirmation_link": "http://file.supremecourt.gov/casenotification/update?verify=CfDJ8LWjh78o-U5EigyPTWy9BmekjhR9plnZeYQHVl3uPceov95hvtFvqNhiJMMqHBzJV2ghZqBPHNh5RsKiWpg5xIivNeMJY6khyqOvoh-hr-GWniqjbqooFYeevAFYHzSBQhlX_vMY2mIJORl9dYZAaLJvbk-JFWLANLnh3vaPhtAknU6xszMVXJwPqQNU2onUC7VoP-YN_pV3k6UXmQvUziwuPaKuwgWOogpRaNQt1lapNhv6zXvL8zIJnH-nCnZeom2o2g7odXotLrdvau4p1xtZ6lOzboGltJGV0LTuxQFT"
        }

        :return: `dict` of data extracted from the email. Will return `{}` if
        email parsing has not occurred or has failed. A field will be set to
        `None` if extraction of that specific field from the email fails.
        """
        if self.email_type == EmailType.DOCKET_ENTRY:
            return {
                "email_type": "docket_entry",
                "docket_number": self._parse_docket_number(),
                "notification_datetime": self._parse_datetime(),
                "case_name": self._parse_case_name(),
                "case_url": self._parse_case_link(),
                "entry_description": self._parse_filing_name(),
            }
        elif self.email_type == EmailType.CONFIRMATION:
            return {
                "email_type": "confirmation",
                "confirmation_link": self._parse_confirmation_link(),
            }
        return {}

    def _determine_email_type(self) -> EmailType:
        """Determine the type of the email (docket update/confirmation) based
        on the subject line. If the subject line does not match any known
        patterns, return `EmailType.INVALID`."""
        subject = self.message.get("Subject", failobj="")

        if self.DOCKET_ENTRY_SUBJECT_REGEX.match(subject) is not None:
            return EmailType.DOCKET_ENTRY
        elif self.CONFIRMATION_SUBJECT_REGEX.match(subject) is not None:
            return EmailType.CONFIRMATION
        logger.error(
            "Email subject did not match known patterns. Subject: %s", subject
        )
        return EmailType.INVALID

    def _parse_text(self, text: str) -> None:
        """Extract and store the first part of the email with the "Content-Type"
        header set to "text/html" and store a parsed HTML tree. Assumes that
        there will always be an email part with this content type. If lxml
        parsing fails, return `None` and log an appropriate error.

        :param text: The raw email text.

        :return: None
        """
        self.message = email.message_from_string(text)
        email_type = self._determine_email_type()

        if email_type == EmailType.INVALID:
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
                "Unable to find non-multipart content part with 'text/html' content type in email"
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

        if email_type == EmailType.DOCKET_ENTRY:
            if self.message.get("Date") is None:
                logger.error("Unable to find 'Date' header in email")
                return

            if n_anchors < 2:
                logger.error(
                    "Unable to find at least two links in email body (should be case link and unsubscribe link); found %d",
                    n_anchors,
                )
                return

            text = self.tree.text_content()
            if self.TITLE_REGEX.match(text) is None:
                logger.error(
                    "Unable to find match for docket entry title regex in email"
                )
                return

            self.email_type = email_type
        elif email_type == EmailType.CONFIRMATION:
            if n_anchors != 1:
                logger.error(
                    "Incorrect number of links in email body. Should be exactly one (confirmation link); found %d",
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

    def _parse_case_link(self) -> str:
        """Extract the `href` attribute from the first `<a>` tag in the email
        body, which should be the link to the case.

        :return: Link to the case.
        """
        return self.tree.find(".//a").get("href")

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

    def _parse_confirmation_link(self) -> str:
        """Extract the `href` attribute from the first `<a>` tag in the email
        body, which should be the confirmation link.
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
