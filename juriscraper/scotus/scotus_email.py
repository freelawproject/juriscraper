import email
import re
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

from lxml import html
from lxml.html import HtmlElement

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import clean_html
from juriscraper.lib.string_utils import clean_string, harmonize


class SCOTUSEmail:
    """Parse SCOTUS docket notification email."""

    TITLE_REGEX = re.compile(r"^A new docket entry, \"(.+?)\" has been added")

    def __init__(self, court_id: str = "scotus"):
        self.court_id: str = court_id
        self.tree: Optional[HtmlElement] = None
        self.message: Optional[EmailMessage] = None
        self.is_valid: bool = False

    @property
    def data(self) -> dict:
        """Extract all the data in the email into the following format:

        {
            "docket_number": "25-250",
            "notification_datetime": "2025-10-09 02:04:05+00:00",
            "case_name": "Donald J. Trump, President of the United States v. V.O.S. Selections, Inc.",
            "case_url": "https://www.supremecourt.gov/search.aspx?filename=/docket/DocketFiles/html/Public/25-250.html",
            "entry_description": "Amicus brief of Corey J. Biazzo, Esq. submitted."
        }

        :return: `dict` of data extracted from the email. Will return `{}` if
        email parsing has not occurred or has failed. A field will be set to
        `None` if extraction of that specific field from the email fails.
        """
        if self.is_valid:
            return {
                "docket_number": self._parse_docket_number(),
                "notification_datetime": self._parse_datetime(),
                "case_name": self._parse_case_name(),
                "case_url": self._parse_case_link(),
                "entry_description": self._parse_filing_name(),
            }
        else:
            return {}

    def _parse_text(self, text: str) -> None:
        """Extract and store the first part of the email with the "Content-Type"
        header set to "text/html" and store a parsed HTML tree. Assumes that
        there will always be an email part with this content type. If lxml
        parsing fails, return `None` and log an appropriate error.

        :param text: The raw email text.

        :return: None
        """
        self.message = email.message_from_string(text)

        if self.message.get("Date") is None:
            logger.error("Unable to find 'Date' header in email")
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

        if n_anchors < 2:
            logger.error(
                "Unable to find at least two links in email body (should be case link and unsubscribe link)"
            )
            return

        text = self.tree.text_content()
        if self.TITLE_REGEX.match(text) is None:
            logger.error(
                "Unable to find match for docket entry title regex in email"
            )
            return

        self.is_valid = True

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
