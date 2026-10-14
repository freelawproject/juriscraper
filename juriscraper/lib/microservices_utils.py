import os
from contextlib import nullcontext
from typing import Literal
from urllib.parse import urljoin

import httpx
from httpx import AsyncClient, Response, TimeoutException
from lxml import html
from typing_extensions import Unpack

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.type_utils import (
    AsyncClientOptions,
    GetRequestOptions,
    PostRequestOptions,
)

MICROSERVICE_URLS = {
    "document-extract": "{}/extract/doc/text/",
    "buffer-extension": "{}/utils/file/extension/",
}

logger = make_default_logger()


async def test_for_meta_redirections(
    r: Response,
    *,
    session: AsyncClient | None = None,
    client_options: AsyncClientOptions | None = None,
    request_options: PostRequestOptions | None = None,
) -> tuple[Literal[False], None] | tuple[Literal[True], str]:
    """Test for meta data redirections

    :param r: A response object
    :return:  A boolean and value
    """
    if client_options is None:
        client_options = {}
    try:
        extension = await get_extension(
            r.content,
            session=session,
            request_options=request_options,
            **client_options,
        )
    except TimeoutException as e:
        # Transient network issues - don't send to Sentry
        logger.warning(
            "Timeout error getting extension from microservice: %s",
            e,
        )
        extension = ""
    except Exception:
        # blanket exception until we get more error information
        logger.error("Error getting extension on juriscraper", exc_info=True)
        extension = ""

    if extension != ".html":
        return False, None

    html_tree = html.fromstring(r.text)

    path = (
        "//meta[translate(@http-equiv, 'REFSH', 'refsh') = 'refresh']/@content"
    )
    try:
        attr: object = html_tree.xpath(path)[0]
        if not isinstance(attr, str):
            return False, None
        wait, text = attr.split(";")
        if text.lower().startswith("url="):
            url = text[4:]
            if not url.startswith("http"):
                # Relative URL, adapt
                url = urljoin(str(r.url), url)
            return True, url
    except IndexError:
        return False, None

    return False, None


async def follow_redirections(
    r: Response,
    s: AsyncClient,
    *,
    doctor_options: AsyncClientOptions | None = None,
    doctor_request_options: PostRequestOptions | None = None,
    **kwargs: Unpack[GetRequestOptions],
) -> Response:
    """
    Parse and follow meta refresh redirections if they exist until
    there are no more.
    """
    options: AsyncClientOptions = (
        doctor_options.copy() if doctor_options is not None else {}
    )
    options.setdefault("http2", True)
    options.setdefault("timeout", 30)
    async with httpx.AsyncClient(**options) as doctor_session:
        redirects = 0
        while True:
            _, url = await test_for_meta_redirections(
                r,
                session=doctor_session,
                request_options=doctor_request_options,
            )
            if url is None:
                return r
            if redirects >= s.max_redirects:
                raise httpx.TooManyRedirects(
                    "Exceeded maximum allowed meta redirects.",
                    request=r.request,
                )
            logger.info(f"Following a meta redirection to: {url.encode()}")
            r = await s.get(url, **kwargs)
            redirects += 1


async def get_extension(
    content: bytes,
    *,
    session: AsyncClient | None = None,
    request_options: PostRequestOptions | None = None,
    **kwargs: Unpack[AsyncClientOptions],
) -> str:
    """
    Get the extension of a file using a microservice.

    :param content: The item to get the extension for
    :return extension: The extension of the file, e.g. ".pdf", ".html", etc.
    """
    if session is not None and bool(kwargs):
        raise ValueError("Configure client options on the supplied session.")
    # Get the file type from the document's raw content
    doctor_host = os.environ.get("DOCTOR_HOST", "http://cl-doctor:5050")
    extension_url = MICROSERVICE_URLS["buffer-extension"].format(doctor_host)
    kwargs.setdefault("http2", True)
    kwargs.setdefault("timeout", 30)
    options: PostRequestOptions = (
        request_options.copy() if request_options is not None else {}
    )
    if not any(key in options for key in ("content", "data", "files", "json")):
        options["files"] = {"file": ("filename", content)}
    async with (
        nullcontext(session)
        if session is not None
        else httpx.AsyncClient(**kwargs)
    ) as client:
        extension_response = await client.request(
            "POST", extension_url, **options
        )
    extension_response.raise_for_status()
    extension = extension_response.text

    return extension
