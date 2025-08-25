import os
from typing import Optional
from urllib.parse import urljoin

import requests
from lxml import html
from requests import Response, Session

from juriscraper.lib.log_tools import make_default_logger

MICROSERVICE_URLS = {
    "document-extract": "{}/extract/doc/text/",
    "buffer-extension": "{}/utils/file/extension/",
}

logger = make_default_logger()


def test_for_meta_redirections(r: Response) -> tuple[bool, Optional[str]]:
    """Test for meta data redirections

    :param r: A response object
    :return:  A boolean and value
    """

    extension = get_extension(r.content)

    if extension == ".html":
        html_tree = html.fromstring(r.text)
        try:
            path = (
                "//meta[translate(@http-equiv, 'REFSH', 'refsh') = "
                "'refresh']/@content"
            )
            attr = html_tree.xpath(path)[0]
            wait, text = attr.split(";")
            if text.lower().startswith("url="):
                url = text[4:]
                if not url.startswith("http"):
                    # Relative URL, adapt
                    url = urljoin(r.url, url)
                return True, url
        except IndexError:
            return False, None
    return False, None


def follow_redirections(r: Response, s: Session) -> Response:
    """
    Parse and recursively follow meta refresh redirections if they exist until
    there are no more.
    """
    redirected, url = test_for_meta_redirections(r)
    if redirected:
        logger.info(f"Following a meta redirection to: {url.encode()}")
        r = follow_redirections(s.get(url), s)
    return r


def get_extension(r) -> str:
    """
    Get the extension of a file using a microservice.

    :param r: The item to get the extension for
    :return extension: The extension of the file, e.g. ".pdf", ".html", etc.
    """
    doctor_host = os.environ.get("DOCTOR_HOST", "http://cl-doctor:5050")
    # Get the file type from the document's raw content
    extension_url = MICROSERVICE_URLS["buffer-extension"].format(doctor_host)
    extension_response = requests.post(
        extension_url, files={"file": ("filename", r)}, timeout=30
    )
    extension_response.raise_for_status()
    extension = extension_response.text

    return extension
