from __future__ import annotations

import gzip
import hashlib
import http.cookiejar
import json
import os
import ssl
import urllib.parse
import urllib.request
from collections.abc import (
    Awaitable,
    Callable,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
)
from datetime import date, datetime
from types import TracebackType
from typing import Generic, NotRequired, Self, TypeAlias

import certifi
import httpx
from charset_normalizer import from_bytes
from lxml import etree
from lxml.html import HtmlElement
from pydantic import JsonValue
from typing_extensions import TypedDict, TypeVar, Unpack

from juriscraper.lib.date_utils import (
    json_date_handler,
    make_date_range_tuples,
)
from juriscraper.lib.exceptions import (
    InsanityException,
)
from juriscraper.lib.html_utils import (
    clean_html,
    fix_links_in_lxml_tree,
    get_html_from_element,
    get_html_parsed_text,
    set_response_encoding,
)
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.microservices_utils import follow_redirections
from juriscraper.lib.string_utils import (
    CaseNameTweaker,
    trunc,
)
from juriscraper.lib.type_utils import (
    AsyncClientOptions,
    BackscrapeOptions,
    CookieTypes,
    GetRequestOptions,
    PostRequestOptions,
    RawOpinion,
    _ClientOptions,
)
from juriscraper.lib.utils import (
    check_download_url,
    check_empty_downloaded_file,
    check_expected_content_types,
    clean_attribute,
    sanity_check_case_names,
    sanity_check_dates,
)

logger = make_default_logger()

DownloadedContent: TypeAlias = "HtmlElement | etree._ElementTree[etree._Element] | Mapping[str, object] | Sequence[object] | int | float | bool | None"

BackscrapeItem = TypeVar("BackscrapeItem", default=object)


class SiteOptions(
    _ClientOptions,
    BackscrapeOptions,
    Generic[BackscrapeItem],
    total=False,
    closed=True,
):
    cookies: CookieTypes | None
    save_response_fn: Callable[[AbstractSite[BackscrapeItem]], None] | None


class RequestParameters(PostRequestOptions):
    pass


class RequestState(TypedDict):
    session: httpx.AsyncClient
    headers: dict[str, str]
    parameters: RequestParameters
    request: httpx.Request | None
    status: int | None
    url: str | None
    response: NotRequired[httpx.Response]


class AbstractSite(Generic[BackscrapeItem]):
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function.
    """

    case_name_shorts: list[str]

    # Set to True in subclasses to use urllib instead of httpx.
    # Useful for sites that block httpx via TLS fingerprinting.
    use_urllib = False

    # Some courts' bot management blocks the "Juriscraper" User-Agent, and
    # some also block browser User-Agents that have gone stale. Scrapers that
    # need to look like a browser should use `self.chrome_user_agent` instead
    # of hardcoding a string, so a single bump here updates all of them.
    # Keep in sync with the current stable Chrome release.
    chrome_version = "151"
    chrome_user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36"
    )
    # Client hints matching `chrome_user_agent`, for sites that check them
    chrome_sec_ch_ua = (
        f'"Google Chrome";v="{chrome_version}", '
        f'"Chromium";v="{chrome_version}", "Not)A;Brand";v="24"'
    )

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        *,
        save_response_fn: Callable[[AbstractSite[BackscrapeItem]], None]
        | None = None,
        backscrape_start: str | None = None,
        backscrape_end: str | None = None,
        days_interval: int | None = None,
        **kwargs: Unpack[AsyncClientOptions],
    ) -> None:
        super().__init__()

        # Computed metadata
        self.hash: str | None = None
        self.case_names: Sequence[str] | None = None
        self.case_dates: Sequence[date | str | None] | None = None
        self.html: DownloadedContent = None
        self.method = "GET"
        self.back_scrape_iterable: Iterable[BackscrapeItem] | None = None
        self.downloader_executed = False
        self.cookies: CookieTypes = {}
        self.cnt = cnt if cnt is not None else CaseNameTweaker()
        self.user_agent = user_agent

        # Attribute to reference a function passed by the caller,
        # which takes a single argument, the Site object, after
        # each GET or POST request. Intended for saving the response for
        # debugging purposes.
        self.save_response = save_response_fn

        # Won't affect the values of the child scraper as these only get
        # passed to httpx at this stage.
        kwargs.setdefault("follow_redirects", True)
        kwargs.setdefault("http2", True)
        kwargs.setdefault("verify", True)
        self._download_timeout = kwargs.get("timeout", 300)
        self._request_timeout = kwargs.get("timeout", 60)
        self.request: RequestState = {
            "session": httpx.AsyncClient(**kwargs),
            "headers": {
                "User-Agent": self.user_agent,
                # Disable CDN caching on sites like SCOTUS (ahem)
                "Cache-Control": "no-cache, max-age=0, must-revalidate",
                # backwards compatibility with HTTP/1.0 caches
                "Pragma": "no-cache",
            },
            "parameters": {},
            "request": None,
            "status": None,
            "url": None,
        }

        # Some courts will block Juriscraper or Courtlistener's user-agent
        # or may need special headers. This flag let's the caller know it
        # should use the modified `self.request["headers"]`
        self.needs_special_headers = False

        # urllib opener for sites that need TLS fingerprint bypass
        if self.use_urllib:
            cookie_jar = http.cookiejar.CookieJar()
            self.urllib_opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(cookie_jar)
            )

        # indicates whether the scraper should have results or not to raise an error
        self.should_have_results = False

        # has defaults in OpinionSite and OralArgumentSite
        self.expected_content_types: list[str] | None = []

        # Sub-classed metadata
        self.court_id: str | None = None
        self.url: str | None = None
        self.parameters: (
            Mapping[str, object]
            | Sequence[tuple[str, object]]
            | str
            | bytes
            | None
        ) = None
        self.mock_url: str = ""
        self._opt_attrs: list[str] = []
        self._req_attrs: list[str] = []
        self._all_attrs: list[str] = []

    async def __aenter__(self) -> Self:
        await self.request["session"].__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.request["session"].__aexit__(exc_type, exc_value, traceback)

    def __str__(self) -> str:
        out = []
        for attr, val in self.__dict__.items():
            out.append(f"{attr}: {val}")
        return "\n".join(out)

    def __iter__(self) -> Iterator[dict[str, object] | RawOpinion]:
        for i in range(len(self)):
            yield self._make_item(i)

    def __getitem__(self, i: int) -> dict[str, object] | RawOpinion:
        return self._make_item(i)

    def __len__(self) -> int:
        if self.case_names is None:
            raise ValueError("Parse the site before accessing its results.")
        return len(self.case_names)

    async def close_session(self) -> None:
        await self.request["session"].aclose()

    def _make_item(self, i: int) -> dict[str, object]:
        """Using i, convert a single item into a dict. This is effectively a
        different view of the data.
        """
        item: dict[str, object] = {}
        for attr_name in self._all_attrs:
            attr_value: Sequence[object] | None = getattr(self, attr_name)
            if attr_value is not None:
                item[attr_name] = attr_value[i]
        return item

    def enable_test_mode(self) -> None:
        self.method = "LOCAL"

    def dump_html(
        self, element: HtmlElement | etree._ElementTree[HtmlElement]
    ) -> None:
        """Use this for debugging purposes"""
        print(get_html_from_element(element))

    def set_custom_adapter(self, cipher: str) -> ssl.SSLContext:
        """Set Custom SSL/TLS cipher for out of date court systems

        :param cipher: The court required cipher
        :return: None
        """
        ctx = ssl.create_default_context(cafile=certifi.where())
        ctx.set_ciphers(cipher)
        return ctx

    def test_mode_enabled(self) -> bool:
        return self.method == "LOCAL"

    def to_json(self) -> str:
        return json.dumps(
            list(self),
            default=json_date_handler,
        )

    async def parse(self) -> Self:
        if not self.downloader_executed:
            # Run the downloader if it hasn't been run already
            self.html = await self._download()

            # Process the available html (optional)
            maybe_awaitable = self._process_html()
            if isinstance(maybe_awaitable, Awaitable):
                await maybe_awaitable

        # Set the attribute to the return value from _get_foo()
        # e.g., this does self.case_names = _get_case_names()
        for attr in self._all_attrs:
            get_attr: Callable[[], object] = getattr(self, f"_get_{attr}")
            value: object = get_attr()
            if isinstance(value, Awaitable):
                value = await value
            self.__setattr__(attr, value)

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            # This needs to be done *after* _clean_attributes() has been run.
            # The current architecture means this gets run twice. Once when we
            # iterate over _all_attrs, and again here. It's pretty cheap though.
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return self

    def tweak_response_object(self) -> None:
        """
        Does nothing, but provides a hook that allows inheriting objects to
        tweak the requests object if necessary.
        """
        pass

    def _clean_text(self, text: str) -> str:
        """A hook for subclasses to override if needed."""
        return clean_html(text)

    def _clean_attributes(self) -> None:
        """Iterate over attribute values and clean them"""
        for attr in self._all_attrs:
            item = getattr(self, attr)
            if item is None:
                continue

            cleaned_item = [
                clean_attribute(attr, sub_item) for sub_item in item
            ]

            self.__setattr__(attr, cleaned_item)

    def _post_parse(self) -> None:
        """This provides an hook for subclasses to do custom work on the data
        after the parsing is complete.
        """
        pass

    def no_results_warning(self) -> None:
        if self.should_have_results:
            logger.error(
                f"{self.court_id}: Returned with zero items, but should have results."
            )
        else:
            logger.warning(f"{self.court_id}: Returned with zero items.")

    def _check_sanity(self) -> None:
        """Check that the objects attributes make sense:
            1. Do all the attributes have the same length?
            1. Do we have any content at all?
            1. Is there a bare minimum of meta data?
            1. Are the dates datetime objects, not strings?
            1. Are any dates from the 22nd century? (01-01-2104)
            1. Are case_names more than just empty whitespace?
            1. Has the `cookies` attribute been normalized to a dict?
            1. ?

        The signature of this method is subject to change as additional checks
        become convenient.

        Inheriting classes should override this method calling super to give it
        the necessary parameters.

        If sanity is OK, no return value. If not, throw InsanityException or
        warnings, as appropriate.
        """
        if self.case_names is None or self.case_dates is None:
            raise InsanityException(
                f"{self.court_id}: Required case names or dates are missing."
            )

        # check that all attributes have the same length
        lengths = {}
        for attr in self._all_attrs:
            if self.__getattribute__(attr) is not None:
                lengths[attr] = len(self.__getattribute__(attr))

        values = list(lengths.values())
        if bool(values) and values.count(values[0]) != len(values):
            # Are all elements equal?
            raise InsanityException(
                "%s: Scraped meta data fields have differing"
                " lengths: %s" % (self.court_id, lengths)
            )

        if not isinstance(self.cookies, dict):
            raise InsanityException(
                "self.cookies not set to be a dict by scraper."
            )

        # check that we have data
        if len(self.case_names) == 0:
            self.no_results_warning()
            return

        # check that all require fields have data
        for field in self._req_attrs:
            if self.__getattribute__(field) is None:
                raise InsanityException(
                    "%s: Required fields do not contain any data: %s"
                    % (self.court_id, field)
                )

        sanity_check_case_names(self.case_names)
        date_filed_is_approximate = getattr(
            self, "date_filed_is_approximate", None
        )
        if date_filed_is_approximate is None:
            date_filed_is_approximate = [False] * len(self.case_names)
        elif not isinstance(date_filed_is_approximate, Sequence):
            raise InsanityException(
                "date_filed_is_approximate must be a sequence."
            )

        sanity_check_dates(
            zip(self.case_dates, self.case_names, date_filed_is_approximate),
            str(self.court_id),
        )

        logger.info(
            "%s: Successfully found %s items."
            % (self.court_id, len(self.case_names))
        )

    def _date_sort(self) -> None:
        """Sort the object by date."""
        if len(self) > 0:
            obj_list_attrs = [
                self.__getattribute__(attr)
                for attr in self._all_attrs
                if isinstance(self.__getattribute__(attr), list)
            ]
            zipped = list(zip(*obj_list_attrs))
            zipped.sort(reverse=True)
            i = 0
            obj_list_attrs = list(zip(*zipped))
            for attr in self._all_attrs:
                if isinstance(self.__getattribute__(attr), list):
                    self.__setattr__(attr, obj_list_attrs[i][:])
                    i += 1

    def _make_hash(self) -> None:
        """Make a unique ID. ETag and Last-Modified from courts cannot be
        trusted
        """
        self.hash = hashlib.sha1(str(self.case_names).encode()).hexdigest()

    def _make_html_tree(self, text: str | bytes) -> HtmlElement:
        """Hook for custom HTML parsers

        By default, the etree.html parser is used, but this allows support for
        other parsers like the html5parser or even BeautifulSoup, if it's called
        for (example: return get_html5_parsed_text(text)). Otherwise, this method
        can be overwritten to execute custom parsing logic.
        """
        return get_html_parsed_text(text)

    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> DownloadedContent:
        """Download the latest version of Site"""
        if self.url is None:
            raise ValueError("A URL is required before downloading a site.")
        if request_dict is None:
            request_dict = {}
        self.downloader_executed = True
        if self.method == "POST":
            if isinstance(self.parameters, Mapping):
                truncated_params = {
                    k: trunc(str(v), 50, ellipsis="...[truncated]")
                    for k, v in self.parameters.items()
                }
            else:
                truncated_params = trunc(
                    str(self.parameters), 50, ellipsis="...[truncated]"
                )
            logger.info(
                "Now downloading case page at: %s (params: %s)"
                % (self.url, truncated_params)
            )
        else:
            logger.info(f"Now downloading case page at: {self.url}")

        self._process_request_parameters(request_dict)

        if self.test_mode_enabled():
            await self._request_url_mock(self.url)
            self._post_process_response()
            return self._return_response_text_object()
        elif self.use_urllib:
            return self._download_urllib()
        elif self.method == "GET":
            await self._request_url_get(self.url)
        elif self.method == "POST":
            await self._request_url_post(self.url)

        self._post_process_response()
        return self._return_response_text_object()

    def _download_content_urllib(
        self, download_url: str, headers: dict[str, str]
    ) -> httpx.Response:
        """Download content using urllib to bypass Cloudflare

        Uses urllib instead of httpx because Cloudflare blocks httpx
        via TLS fingerprinting. Used by scrapers with `use_urllib = True`.

        :param download_url: The URL for the item you wish to download.
        :param headers: headers dict
        :return: A response object with a `content` field
        """
        req = urllib.request.Request(download_url, headers=headers)
        with self.urllib_opener.open(req, timeout=90) as response:
            raw: bytes = response.read()
            status: int = response.status
            response_url: str = response.geturl()
            headers_list: list[tuple[str, str]] = response.headers.items()
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            buffered = httpx.Response(
                status_code=status,
                content=raw,
                request=httpx.Request(req.get_method(), response_url),
            )
            # Attach original headers after buffering to avoid decoding gzip twice.
            buffered.headers = httpx.Headers(
                headers_list, encoding="iso-8859-1"
            )
        return buffered

    async def download_content(
        self,
        download_url: str,
        doctor_is_available: bool = True,
        media_root: str = "",
        *,
        doctor_options: AsyncClientOptions | None = None,
        doctor_request_options: PostRequestOptions | None = None,
        **kwargs: Unpack[GetRequestOptions],
    ) -> str | bytes:
        """Download the URL and return the cleaned content

        Downloads the file, covering a few special cases such as invalid SSL
        certificates and empty file errors.

        :param download_url: The URL for the item you wish to download.
        :param doctor_is_available: If True, it will try to follow meta
            redirections
        :param media_root: The root directory for local files in Courtlistener,
            used in test mode

        :return: The downloaded and cleaned content
        :raises: NoDownloadUrlError, UnexpectedContentTypeError, EmptyFileError
        """
        check_download_url(download_url)

        # noinspection PyBroadException
        if self.test_mode_enabled():
            # this is useful for CL integration tests
            def handler(request: httpx.Request) -> httpx.Response:
                r = httpx.Response(status_code=404, request=request)
                try:
                    url = os.path.join(media_root, download_url)
                    with open(url, mode="rb") as stream:
                        r = httpx.Response(
                            status_code=200,
                            request=request,
                            content=stream.read(),
                        )
                        if url.endswith("json"):
                            r.headers["content-type"] = "application/json"
                except OSError as e:
                    raise httpx.ConnectError(message=str(e), request=request)
                return r

            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as mock_client:
                r = await mock_client.get(
                    self.url if bool(self.url) else "https://localhost/"
                )
            return self.cleanup_content(r.content)

        if self.needs_special_headers:
            headers = self.request["headers"]
        else:
            headers = {"User-Agent": "CourtListener"}

        if self.use_urllib:
            r = self._download_content_urllib(download_url, headers)
        else:
            # Note that we do a GET even if self.method is POST. This is
            # deliberate.
            kwargs.setdefault("headers", headers)
            kwargs.setdefault("cookies", self.cookies)
            kwargs.setdefault("timeout", self._download_timeout)
            r = await self.request["session"].get(download_url, **kwargs)

        check_empty_downloaded_file(r, download_url)
        check_expected_content_types(self, r, download_url)

        if doctor_is_available and not self.use_urllib:
            # test for and follow meta redirects, uses doctor get_extension
            # service
            r = await follow_redirections(
                r,
                self.request["session"],
                doctor_options=doctor_options,
                doctor_request_options=doctor_request_options,
            )
            r.raise_for_status()

        content = self.cleanup_content(r.content)

        return content

    def _process_html(self) -> None | Awaitable[None]:
        """Hook for processing available self.html after it's been downloaded.
        This step is completely optional, but is useful if you want to transform
        the html before running the data getters (_get_*), or if its easier to
        extract the cases form the html in a linear function (here) as opposed
        to using separate data getters.  See sc.py for example.
        """
        pass

    def _process_request_parameters(
        self, parameters: RequestParameters | None = None
    ) -> None:
        """Hook for processing injected parameter overrides"""
        if parameters is None:
            parameters = {}
        self.request["parameters"].update(parameters)

    def _download_urllib(self) -> HtmlElement | JsonValue:
        """Handle download using urllib backend.

        :return: parsed HTML tree or JSON object
        """
        if self.url is None:
            raise ValueError("A URL is required before downloading a site.")
        data = None
        if self.method == "POST":
            parameters = self.parameters
            if isinstance(parameters, str):
                data = parameters.encode("utf-8")
            elif isinstance(parameters, bytes):
                data = parameters
            elif parameters is not None:
                data = urllib.parse.urlencode(parameters).encode("utf-8")

        raw = self._urllib_fetch(self.url, data=data)
        text = raw.decode("utf-8")

        response = self.request.get("response")
        if response is None:
            raise ValueError("Download a response before accessing it.")
        content_type = response.headers.get("Content-Type", "")
        if "json" in content_type:
            json_data: JsonValue = json.loads(text)
            return json_data

        text = self._clean_text(text)
        html_tree = self._make_html_tree(text)
        return html_tree

    def _urllib_fetch(
        self,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        """Fetch a URL using urllib to bypass Cloudflare TLS fingerprinting.

        httpx gets blocked by Cloudflare due to its TLS fingerprint
        (httpcore). Python's stdlib urllib uses a different TLS stack
        that Cloudflare does not block.

        :param url: URL to fetch
        :param data: POST data as bytes, or None for GET
        :param headers: optional dict of headers to use instead of defaults
        :return: raw response bytes
        """
        req = urllib.request.Request(
            url,
            data=data,
            headers=self.request["headers"] if headers is None else headers,
        )
        with self.urllib_opener.open(req, timeout=60) as urllib_response:
            raw: bytes = urllib_response.read()
            status: int = urllib_response.status
            response_url: str = urllib_response.geturl()
            headers_list: list[tuple[str, str]] = (
                urllib_response.headers.items()
            )
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            response = httpx.Response(
                status_code=status,
                content=raw,
                request=httpx.Request(req.get_method(), response_url),
            )
            # Attach original headers after buffering to avoid decoding gzip twice.
            response.headers = httpx.Headers(
                headers_list, encoding="iso-8859-1"
            )

        # Populate request dict for save_response compatibility.
        # Currently only needed for lactapp_3 which uses urllib
        self.request["url"] = url
        self.request["response"] = response
        if self.save_response is not None:
            self.save_response(self)

        return response.content

    async def _request_url_get(self, url: str) -> httpx.Response:
        """Execute GET request and assign appropriate request dictionary
        values
        """
        self.request["url"] = url
        kwargs = self.request["parameters"].copy()
        kwargs.setdefault("headers", self.request["headers"])
        kwargs.setdefault("timeout", self._request_timeout)
        self.request["response"] = await self.request["session"].request(
            "GET", url, **kwargs
        )
        if self.save_response is not None:
            self.save_response(self)
        return self.request["response"]

    async def _request_url_post(self, url: str) -> httpx.Response:
        """Execute POST request and assign appropriate request dictionary values"""
        self.request["url"] = url
        parameters = self.parameters
        if (
            parameters is not None
            and not isinstance(parameters, str | bytes)
            and not isinstance(parameters, Mapping)
        ):
            raise TypeError(
                "POST parameters must be a mapping, text, or bytes."
            )
        kwargs = self.request["parameters"].copy()
        kwargs.setdefault("headers", self.request["headers"])
        kwargs.setdefault("timeout", self._request_timeout)
        if not any(
            key in kwargs for key in ("data", "content", "files", "json")
        ):
            if isinstance(parameters, Mapping):
                kwargs["data"] = parameters
            elif isinstance(parameters, str | bytes):
                kwargs["content"] = parameters
        self.request["response"] = await self.request["session"].request(
            "POST", url, **kwargs
        )
        if self.save_response is not None:
            self.save_response(self)
        return self.request["response"]

    async def _request_url_mock(self, url: str) -> httpx.Response:
        """Execute mock request, used for testing"""
        self.request["url"] = url

        def handler(request: httpx.Request) -> httpx.Response:
            try:
                with open(self.mock_url, mode="rb") as stream:
                    content = stream.read()
                    try:
                        text = content.decode("utf-8")
                    except UnicodeDecodeError:
                        text = str(from_bytes(content).best())
                    r = httpx.Response(
                        status_code=200,
                        request=request,
                        text=text,
                    )
                    if self.mock_url.endswith("json"):
                        r.headers["content-type"] = "application/json"
            except OSError as e:
                raise httpx.RequestError(message=str(e), request=request)
            return r

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as mock_client:
            self.request["response"] = await mock_client.get(url)
        return self.request["response"]

    def _post_process_response(self) -> None:
        """Cleanup to response object"""
        self.tweak_response_object()
        response = self.request.get("response")
        if response is None:
            raise ValueError("Download a response before accessing it.")
        response.raise_for_status()
        set_response_encoding(response)

    def _return_response_text_object(self) -> HtmlElement | JsonValue:
        if "response" in self.request:
            if "json" in self.request["response"].headers.get(
                "content-type", ""
            ):
                data: JsonValue = self.request["response"].json()
                return data
            else:
                try:
                    payload = self.request["response"].content.decode("utf8")
                except UnicodeDecodeError:
                    payload = self.request["response"].text

                text = self._clean_text(payload)
                html_tree = self._make_html_tree(text)
                if hasattr(html_tree, "rewrite_links"):
                    html_tree.rewrite_links(
                        fix_links_in_lxml_tree, base_href=self.request["url"]
                    )
                return html_tree
        return None

    async def _get_html_tree_by_url(
        self, url: str, parameters: RequestParameters | None = None
    ) -> HtmlElement:
        if parameters is None:
            parameters = {}
        self._process_request_parameters(parameters)
        await self._request_url_get(url)
        self._post_process_response()
        tree = self._return_response_text_object()
        if not isinstance(tree, HtmlElement):
            raise TypeError(f"Expected an HTML document at {url}")
        tree.make_links_absolute(url)
        return tree

    async def _download_backwards(self, d: BackscrapeItem, /) -> None:
        # methods for downloading the entire Site
        pass

    def make_backscrape_iterable(
        self: AbstractSite[tuple[date, date] | BackscrapeItem],
        kwargs: BackscrapeOptions,
    ) -> None:
        """Creates back_scrape_iterable in the most common variation,
        a list of tuples containing (start, end) date pairs, each of
        `days_interval` size

        Uses default attributes of the scrapers as a fallback, if
        expected keyword arguments are not passed in the kwargs input

        :param kwargs: if the following keys are present, use them
            backscrape_start: str in "%Y/%m/%d" format ;
                            Default: self.first_opinion_date
            backscrape_end: str
            days_interval: int; Default: self.days_interval

        :return: None; sets self.back_scrape_iterable in place
        """
        self.back_scrape_iterable = self._get_backscrape_date_ranges(kwargs)

    def _get_backscrape_date_ranges(
        self, kwargs: BackscrapeOptions
    ) -> list[tuple[date, date]]:
        """Build date ranges without changing the scraper's item type."""
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")
        days_interval = kwargs.get("days_interval")

        if bool(start):
            if not isinstance(start, str):
                raise TypeError("backscrape_start must be a date string")
            start = datetime.strptime(start, "%Y/%m/%d").date()
        else:
            start = getattr(self, "first_opinion_date", None)
        if not isinstance(start, date):
            raise ValueError(
                "A backscrape start date or first_opinion_date is required"
            )

        if bool(end):
            if not isinstance(end, str):
                raise TypeError("backscrape_end must be a date string")
            end = datetime.strptime(end, "%Y/%m/%d").date()
        else:
            end = datetime.now().date()

        if not bool(days_interval):
            days_interval = getattr(self, "days_interval", None)
        if not isinstance(days_interval, int) or days_interval <= 0:
            raise ValueError("days_interval must be a positive integer")

        return make_date_range_tuples(start, end, days_interval)

    @staticmethod
    def cleanup_content(content: bytes) -> str | bytes:
        """
        Given the HTML from a page, the binary PDF file, or similar, do any
        last-minute cleaning.

        This method should be called as the last step by any caller and works
        to do any cleanup that is necessary. Usually, this is needed on HTML
        pages, in jurisdictions that post their content in an HTML page with
        headers, footers and other content must be stripped after the page
        has been downloaded by the caller.
        """
        return content

    def _get_cookies(self) -> CookieTypes:
        """
        Some websites require cookies in order to be scraped. This method
        provides a hook where cookies can be retrieved by calling functions.
        Generally the cookies will be set by the _download() method.

        self.cookies is a list of dicts of the form:
        [
            {
                u'domain':   u'www.search.txcourts.gov',
                u'httponly': True,
                u'name':     u'ASP.NET_SessionId',
                u'path':     u'/',
                u'secure':   False,
                u'value':    u'hryku05534xhgr45yxvusuux'
            },
        ]
        """
        return self.cookies

    def _get_case_name_shorts(self) -> list[str]:
        """Generates short case names for all the case names that we scrape."""
        if self.case_names is None:
            raise ValueError(
                "Case names must be populated before shortening them."
            )
        case_name_shorts = []
        for case_name in self.case_names:
            case_name_shorts.append(self.cnt.make_case_name_short(case_name))
        return case_name_shorts

    def _get_blocked_statuses(self) -> list[bool]:
        """Should these items be blocked by search engines? Default is False for
        all subclasses, indicating that the items should not be blocked.

        This method is important because some courts (like family or asylum
        courts) should choose privacy over openness. Note that we consider
        these functions to be a hint to callers, so following these guidelines
        is not guaranteed.
        """
        return [False] * len(self)
