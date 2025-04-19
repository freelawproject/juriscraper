"""Download clients for supremecourt.gov"""

import re
from random import choices, random

import requests
from lxml import html
from lxml.etree import ParserError
from requests.exceptions import ConnectionError
from urllib3.exceptions import NameResolutionError

from juriscraper.lib.exceptions import AccessDeniedError
from juriscraper.lib.log_tools import make_default_logger

from . import utils

logger = make_default_logger()

AGENTS = [
    {
        "ua": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.3.1 Safari/605.1.1"
        ),
        "pct": 30.0,
    },
    {
        "ua": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.3"
        ),
        "pct": 28.39,
    },
    {
        "ua": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/16.6 Safari/605.1.1"
        ),
        "pct": 24.84,
    },
    {
        "ua": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0."
        ),
        "pct": 7.74,
    },
    {
        "ua": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 "
            "Firefox/117."
        ),
        "pct": 2.58,
    },
    {
        "ua": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.3"
        ),
        "pct": 1.29,
    },
    {
        "ua": (
            "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.3"
        ),
        "pct": 1.29,
    },
    {
        "ua": (
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 "
            "Firefox/115."
        ),
        "pct": 1.29,
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.",
        "pct": 1.29,
    },
    {
        "ua": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3"
        ),
        "pct": 1.29,
    },
]

HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Cache-Control": "no-cache",
    "DNT": "1",
    "Host": "www.supremecourt.gov",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Sec-GPC": "1",
    "Upgrade-Insecure-Requests": "1",
    # "User-Agent": "Juriscraper",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
}


not_found_regex = re.compile(r"(?<=ERROR).*not found")


def _access_denied_test(text: str) -> bool:
    """Take an HTML string from a `Response.text` and test for
    `Access Denied`."""
    try:
        root = html.document_fromstring(text)
        status = root.head.text_content().strip() == "Access Denied"
    except (ParserError, IndexError):
        return False
    else:
        return status


def is_access_denied_page(response: requests.Response) -> bool:
    """Take an HTML string from a `Response.text` and test for
    `Access Denied`."""
    ct, cl = (response.headers.get(f) for f in ("content-type", "content-length"))
    if ct and cl:
        if ct.startswith("text/html") and int(cl) > 0:
            return _access_denied_test(response.text)
    return False


def _not_found_test(text: str) -> bool:
    """Take an HTML string from a `Response.text` and test for
    `Access Denied`."""
    try:
        root = html.document_fromstring(text)
        error_string = root.get_element_by_id("pagetitle").text_content()
    except (ParserError, KeyError):
        return False
    else:
        if not_found_regex.search(error_string):
            return True
        else:
            return False


def is_not_found_page(response: requests.Response) -> bool:
    """Take an HTML string from a `Response.text` and test for
    `ERROR: File or directory not found.`.
    """
    ct, cl = (response.headers.get(f) for f in ("content-type", "content-length"))
    if ct and cl:
        if ct.startswith("text/html") and int(cl) > 0:
            return _not_found_test(response.text)
    return False


def is_docket(response: requests.Response) -> bool:
    """Handle two valid possibilities: docket number returns status code 200 and
    either exists or returns HTML error page."""
    if not isinstance(response, requests.Response):
        raise TypeError(f"Expected requests.Response (sub)class; got {type(response)}")

    is_json = "application/json" in response.headers.get("content-type", "")
    return response.status_code == 200 and is_json


def is_stale_content(response: requests.Response) -> bool:
    """Check for response status code 304 but this can include unused
    docket numbers where the Not Found page has a Last-Modified header."""
    return response.status_code == 304 and len(response.content) == 0


def jitter(scale: float = 0.15) -> float:
    """Return a random decimal fraction multiplied by `scale`. Add this to
    retry delays so they space out (i.e. increase dispersion)."""
    return random() * scale


def random_ua() -> str:
    """Return a randomly selected User Agent string."""
    ua_weights = [u["pct"] for u in AGENTS]
    return choices(AGENTS, cum_weights=ua_weights)[0]["ua"]


def download_client(
    url: str,
    *,
    since_timestamp: str = None,
    session: requests.Session = None,
    **kwargs,
) -> requests.Response:
    """Wrapper for requests.Session that can add the 'If-Modified-Since' header
    to requests so server can return status code 304 ('Not Modified') for stale pages.

    :param url: URL to be requested.
    :param since_timestamp: Exclude search results modified before this date.
        Input 'YYYY-MM-DD' format for good results. Download requests use the
        'If-Modified-Since' header to skip source documents that have not been
        updated since `since_timestamp`.
    :param retries: Maximum number of retries to accommodate transient problems.
    :param retry_increment: Additional sleep time added for each retry.
    :return: A requests.Response object.

    Note: kwargs passed to Session query methods (.get, .post, etc).

    The <supremecourt.gov> host appears to have consistent support for the
    'Last-Modified' header. When a timestamp string (see formatting below)
    is passed as the value of the 'If-Modified-Since' request header,
    assets whose 'Last-Modified' header is earlier that 'If-Modified-Since'
    will return status code 304 before terminating the response without
    downloading any further content. This can save significant time
    when executing multiple requests.

    Some drawbacks to using this approach:
    * Requests to non-existent docket pages intermittently return an 'Access Denied'
        text/html page -- possibly when the request rate from a client IP address is
        too high. This response type does not contain a 'Last-Modified' header.
    * <supremecourt.gov> does not appear to return 404 Not Found codes for dockets
        (and all other asserts I have worked with so far). Instead, a 'Not Found'
        HTML page is returned: either with status code 200, or with status code
        304 if the 'Last-Modified' date of that 'Not Found' page is less than
        the 'If-Modified-Since' argument! This behavior makes the use of
        'If-Modified-Since' unsuitable for discovering newly populated docket
        numbers.
    """
    if not session:
        _session = requests.Session()
    else:
        _session = session

    _session.headers.update(HEADERS | {"User-Agent": random_ua()})
    # allow 304 response codes for pages updated before `since_timestamp`
    ts_format = "%a, %d %b %Y %H:%M:%S GMT"
    if since_timestamp:
        mod_stamp = utils.makedate(since_timestamp)
        mod_header = {"If-Modified-Since": mod_stamp.strftime(ts_format)}
        _session.headers.update(mod_header)

    logger.debug(f"Querying {url}")
    try:
        response = _session.get(url, **kwargs)
        return response
    finally:
        if not session:
            # only close the session created here
            _session.close()


def response_handler(response: requests.Response) -> requests.Response:
    """If download is not valid, determine appropriate exception to raise so
    caller can respond e.g. by retrying or stalling."""

    logger.debug(f"Handling Response <{response.url}>")
    try:
        response.raise_for_status()
    except ConnectionError as ce:
        if (
            isinstance(ce.__context__, NameResolutionError)
            or isinstance(ce.__cause__, NameResolutionError)
            or "NameResolutionError" in repr(ce)
        ):
            # server-side measures; throttle and retry
            logger.error(
                f"Server-side measures: {response.url} raised {repr(ce)}",
                exc_info=ce,
            )
            raise
    except Exception as e:
        logger.error(f"UNCAUGHT: {response.url} raised {repr(e)}", exc_info=e)
        logger.debug(response.headers)
        logger.debug(f"Response().text: {response.text}")
        raise
    else:
        if is_access_denied_page(response):
            # let caller log and handle
            logger.error(
                f"Server-side measures: {response.url} returned 'Access Denied' page"
            )
            logger.debug(response.headers)
            logger.debug(f"Response().text: {response.text}")
            raise AccessDeniedError(f"{response.url}")
        else:
            return response
