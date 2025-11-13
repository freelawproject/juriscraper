import email
import os.path
import re
from datetime import datetime
from email.message import EmailMessage
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
            "filing_name": "Amicus brief of Corey J. Biazzo, Esq. submitted.",
            "case_name": "Donald J. Trump, President of the United States, et al., Petitioners v. V.O.S. Selections, Inc., et al.",
            "case_link": "https://www.supremecourt.gov/search.aspx?filename=/docket/DocketFiles/html/Public/25-250.html",
            "docket_number": "25-250",
            "notification_datetime": "2025-10-09 02:04:05+00:00"
        }

        :return: `dict` of data extracted from the email. A field will be set
        to `None` if extraction of that specific field from the email failed or
        if there was an error while parsing the email.
        """
        return {
            "docket_number": self._parse_docket_number(),
            "notification_datetime": self._parse_datetime(),
            "case_name": self._parse_case_name(),
            "case_url": self._parse_case_link(),
            "entry_description": self._parse_filing_name(),
        }

    def _parse_text(self, text: str) -> None:
        """Extract and store the first part of the email with the "Content-Type"
        header set to "text/html" and store a parsed HTML tree. Assumes that
        there will always be an email part with this content type. If lxml
        parsing fails, return `None` and log an appropriate error.

        :param text: The raw email text.

        :return: None
        """
        self.message = email.message_from_string(text)

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
        self.is_valid = True

    def _parse_datetime(self) -> Optional[datetime]:
        """Extract the "Date" header in the notification email message into a
        `datetime`, returning `None` if the header is absent or parsing fails
        and logging an appropriate error.

        :return: `datetime` or `None` if unable to extract or parse the "Date" header.
        """
        if self.is_valid:
            message_date = self.message.get("Date")

            if message_date:
                try:
                    return datetime.strptime(
                        message_date, "%a, %d %b %Y %H:%M:%S %z"
                    )
                except ValueError:
                    logger.error(
                        "Unable to parse 'Date' header of email (value is '%s')",
                        message_date,
                    )
                    return None
            else:
                logger.error("Unable to find 'Date' header of email")
                return None
        else:
            return None

    def _parse_filing_name(self) -> Optional[str]:
        """Extract the docket entry title from the email body using a regex
        and clean it with the `clean_string` method. Return `None` and log
        an error if the regex fails to match the email.

        :return: Clean docket entry title or `None` if unable to extract the title.
        """
        if self.is_valid:
            text = self.tree.text_content()
            match = self.TITLE_REGEX.match(text)

            if match is None:
                logger.error(
                    "Unable to find match for docket entry title regex in email"
                )
                return None
            else:
                return clean_string(match.group(1))
        else:
            return None

    def _parse_case_name(self) -> Optional[str]:
        """Extract the case name from the first `<a>` tag in the email body
        and uses the `harmonize` method to clean it.

        :return: Cleaned case name or `None` if unable to extract the case name.
        """
        if self.is_valid:
            return harmonize(self.tree.findtext(".//a"))
        else:
            return None

    def _parse_case_link(self) -> Optional[str]:
        """Extract the `href` attribute from the first `<a>` tag in the email
        body, which should be the link to the case.

        :return: Link to the case or `None` if unable to extract the link.
        """
        if self.is_valid:
            return self.tree.find(".//a").get("href")
        else:
            return None

    def _parse_docket_number(self) -> Optional[str]:
        """Extract the docket number using the `href` attribute from the first
        `<a>` tag in the email body.

        :return: Docket number or `None` if unable to extract the docket number.
        """
        if self.is_valid:
            file = parse_qs(
                urlparse(self.tree.find(".//a").get("href")).query
            )["filename"][0]
            (docket_number, _) = os.path.splitext(os.path.basename(file))
            return clean_string(docket_number)
        else:
            return None
