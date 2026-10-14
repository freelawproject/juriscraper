import email

from lxml import html
from lxml.html import HtmlElement

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import clean_html


def parse_email_html(text: str) -> HtmlElement | None:
    """Parse raw email text and return an lxml tree of the HTML body.

    Finds the first text/html content part, decodes the payload, and
    returns a parsed lxml tree. Returns None if no HTML part is found
    or decoding fails. Missing charsets default to UTF-8.
    """
    message = email.message_from_string(text)

    content_part = next(
        (
            part
            for part in message.walk()
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
        return None

    payload = content_part.get_payload(decode=True)
    if not isinstance(payload, bytes):
        logger.error("Unable to find a byte payload in the HTML email part")
        return None
    charset = (
        get_content_charset_value
        if bool(
            get_content_charset_value := content_part.get_content_charset()
        )
        else "utf-8"
    )

    try:
        body = payload.decode(charset)
    except (UnicodeDecodeError, LookupError):
        logger.error(
            "Unable to decode email payload with charset '%s'", charset
        )
        return None

    return html.fromstring(clean_html(body))
