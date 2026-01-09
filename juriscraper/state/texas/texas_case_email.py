import email
import pprint
import re
import sys
from datetime import datetime
from email.message import EmailMessage, Message
from re import Match, Pattern
from typing import Any, Optional

from lxml import html
from lxml.html import HtmlElement

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import clean_html
from juriscraper.lib.string_utils import harmonize


class TexasCaseMail:
    """Parse Case Mail from casemail.txcourts.gov.
    Registration for this site is open to the public.
    Users may subscribe to case updates from the case pages
     and receive notice when new events happen on cases.
    """

    TITLE_REGEX = re.compile(r"^A new docket entry, \"(.+?)\" has been added")
    DOCKET_ENTRY_SUBJECT_REGEX = re.compile(
        r"^Supreme Court Electronic Filing System$"
    )
    CONFIRMATION_SUBJECT_REGEX = re.compile(
        r"^Supreme Court Case Notification .+$"
    )

    def __init__(self, court_id: str = "tex"):
        self.court_id: str = court_id
        self.tree: Optional[HtmlElement] = None
        self.message: Optional[EmailMessage] = None

    @property
    def data(self) -> Optional[dict]:
        """Extract all the data in the email.

        If the email is a docket update email, the output will be formatted:

        {
            "email_type": "docket_entry",
            "docket_number": "25-250",
            "notification_datetime": "2025-10-09 02:04:05+00:00",
            "case_name": "Donald J. Trump, President of the United States v. V.O.S. Selections, Inc.",
            "case_url": "https://www.supremecourt.gov/search.aspx?filename=/docket/DocketFiles/html/Public/25-250.html"
        }

        :return: `dict` of data extracted from the email. Will return `{}` if
        email parsing has not occurred or has failed. A field will be set to
        `None` if extraction of that specific field from the email fails.
        """

        data: Optional[dict[str, Any]] = self._parse_case_details()
        if data is None:
            return None
        message_time: datetime | None = self._parse_datetime()
        if message_time is not None:
            data["notification_datetime"] = message_time
        url = self._parse_first_link()
        if url is not None:
            data["case_url"] = url

        return data

    def _parse_text(self, text: str) -> None:
        """Extract and store the first part of the email with the "Content-Type"
        header set to "text/html" and store a parsed HTML tree. Assumes that
        there will always be an email part with this content type. If lxml
        parsing fails, return `None` and log an appropriate error.

        :param text: The raw email text.

        :return: None
        """
        self.message: Message[str, str] = email.message_from_string(text)

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

    def _parse_datetime(self) -> Optional[datetime]:
        """Extract the "Date" header in the notification email message into a
        `datetime`, returning `None` if the header is absent or parsing fails
        and logging an appropriate error.

        :return: `datetime` or `None` if unable to parse the "Date" header.
        """
        if self.message is None:
            return None
        message_date: Any | None = self.message.get("Date")
        if message_date is None:
            return None
        try:
            return datetime.strptime(message_date, "%d %b %Y %H:%M:%S %z")
        except ValueError:
            logger.error(
                "Unable to parse 'Date' header of email (value is '%s')",
                message_date,
            )
            return None

    def _parse_case_details(self) -> Optional[dict[str, str]]:
        """Extract the case name and number via regex and harmonize

        :return: dict of case_name, case_number
        """
        if self.tree is None:
            return None
        extractor: Pattern[str] = re.compile(
            "Case Number: (?P<case_number>[0-9CVR-]*) *(?P<case_name>.*)(?=https://)"
        )
        match: Match[str] | None = extractor.search(self.tree.text_content())
        if match:
            match_dict: dict[str, str] = match.groupdict()
            match_dict["case_name"] = harmonize(
                match_dict["case_name"].strip()
            )
            return match_dict
        return None

    def _parse_first_link(self) -> Optional[str]:
        """Extract the `href` attribute from the first `<a>` tag in the email
        body.
        """
        if self.tree is None:
            return None
        return self.tree.find(".//a").get("href")


def _main():
    """Parse a local email file and pretty print extracted data.

    :return: None
    """
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.scotus_email <filepath>")
        print("Please provide a path to an email file to parse.")
        sys.exit(1)

    report = TexasCaseMail()
    filepath = sys.argv[1]
    print(f"Parsing email file at {filepath}")
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
