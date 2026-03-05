import email
from email.message import Message
from typing import Optional

from lxml import html
from lxml.html import HtmlElement

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import clean_html


class EmailParser:
    """Base class for parsing court notification emails.

    Handles the common work of parsing raw email text into a Message,
    finding the text/html content part, decoding it, and building an
    lxml tree. Subclasses override `_parse_subject` and `_parse_body`
    to implement court-specific logic.
    """

    def __init__(self, court_id: str = "") -> None:
        self.court_id: str = court_id
        self.tree: Optional[HtmlElement] = None
        self.message: Optional[Message] = None

    def _parse_text(self, text: str) -> None:
        self.message = email.message_from_string(text)
        subject = self.message.get("Subject", failobj="")

        if not self._parse_subject(subject):
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
        self._parse_body(self.tree)

    def parse(self, text: str) -> None:
        self._parse_text(text)

    def _parse_subject(self, subject: str) -> bool:
        """Validate or extract info from the email subject.

        Return False to short-circuit before parsing the HTML body.
        Default returns True (no subject validation).
        """
        return True

    def _parse_body(self, tree: HtmlElement) -> None:
        """Process the parsed HTML tree.

        Called after the tree is built. Override for court-specific
        body validation or extraction.
        """
        pass
