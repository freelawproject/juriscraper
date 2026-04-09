import gzip
import hashlib
import http.cookiejar
import inspect
import json
import os
import ssl
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Union

import certifi
import httpx
from charset_normalizer import from_bytes

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
from juriscraper.lib.utils import (
    check_download_url,
    check_empty_downloaded_file,
    check_expected_content_types,
    clean_attribute,
    sanity_check_case_names,
    sanity_check_dates,
)

logger = make_default_logger()


class AbstractSite:
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function.
    """

    # Set to True in subclasses to use urllib instead of httpx.
    # Useful for sites that block httpx via TLS fingerprinting.
    use_urllib = False

    def __init__(self, cnt=None, user_agent="Juriscraper", **kwargs):
        super().__init__()

        # Computed metadata
        self.hash = None
        self.html = None
        self.method = "GET"
        self.back_scrape_iterable = None
        self.downloader_executed = False
        self.cookies = {}
        self.cnt = cnt or CaseNameTweaker()
        self.user_agent = user_agent

        # Attribute to reference a function passed by the caller,
        # which takes a single argument, the Site object, after
        # each GET or POST request. Intended for saving the response for
        # debugging purposes.
        self.save_response = kwargs.pop("save_response_fn", None)

        # Won't affect the values of the child scraper as these only get
        # passed to httpx at this stage.
        kwargs.pop("backscrape_start", None)
        kwargs.pop("backscrape_end", None)
        kwargs.pop("days_interval", None)
        kwargs.setdefault("follow_redirects", True)
        kwargs.setdefault("http2", True)
        kwargs.setdefault("verify", True)
        self.request = {
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
        self.expected_content_types = []

        # Sub-classed metadata
        self.court_id = None
        self.url = None
        self.parameters = None
        self.uses_selenium = None
        self._opt_attrs = []
        self._req_attrs = []
        self._all_attrs = []

    async def __aenter__(self):
        await self.request["session"].__aenter__()

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.request["session"].__aexit__(exc_type, exc_value, traceback)

    def __str__(self):
        out = []
        for attr, val in self.__dict__.items():
            out.append(f"{attr}: {val}")
        return "\n".join(out)

    def __iter__(self):
        for i in range(0, len(self.case_names)):
            yield self._make_item(i)

    def __getitem__(self, i):
        return self._make_item(i)

    def __len__(self):
        return len(self.case_names)

    async def close_session(self):
        if self.request["session"]:
            await self.request["session"].aclose()

    def _make_item(self, i):
        """Using i, convert a single item into a dict. This is effectively a
        different view of the data.
        """
        item = {}
        for attr_name in self._all_attrs:
            attr_value = getattr(self, attr_name)
            if attr_value is not None:
                item[attr_name] = attr_value[i]
        return item

    def enable_test_mode(self):
        self.method = "LOCAL"

    def dump_html(self, element):
        """Use this for debugging purposes"""
        print(get_html_from_element(element))

    def set_custom_adapter(self, cipher: str):
        """Set Custom SSL/TLS cipher for out of date court systems

        :param cipher: The court required cipher
        :return: None
        """
        ctx = ssl.create_default_context(cafile=certifi.where())
        ctx.set_ciphers(cipher)
        return ctx

    def test_mode_enabled(self):
        return self.method == "LOCAL"

    def to_json(self):
        return json.dumps(
            list(self),
            default=json_date_handler,
        )

    async def parse(self):
        if not self.downloader_executed:
            # Run the downloader if it hasn't been run already
            self.html = await self._download()

            # Process the available html (optional)
            if inspect.iscoroutinefunction(self._process_html):
                await self._process_html()
            else:
                self._process_html()

        # Set the attribute to the return value from _get_foo()
        # e.g., this does self.case_names = _get_case_names()
        for attr in self._all_attrs:
            get_attr = getattr(self, f"_get_{attr}")
            if inspect.iscoroutinefunction(get_attr):
                self.__setattr__(attr, await get_attr())
            else:
                self.__setattr__(attr, get_attr())

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

    def tweak_response_object(self):
        """
        Does nothing, but provides a hook that allows inheriting objects to
        tweak the requests object if necessary.
        """
        pass

    def _clean_text(self, text):
        """A hook for subclasses to override if needed."""
        return clean_html(text)

    def _clean_attributes(self):
        """Iterate over attribute values and clean them"""
        for attr in self._all_attrs:
            item = getattr(self, attr)
            if item is None:
                continue

            cleaned_item = [
                clean_attribute(attr, sub_item) for sub_item in item
            ]

            self.__setattr__(attr, cleaned_item)

    def _post_parse(self):
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

    def _check_sanity(self):
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
        # check that all attributes have the same length
        lengths = {}
        for attr in self._all_attrs:
            if self.__getattribute__(attr) is not None:
                lengths[attr] = len(self.__getattribute__(attr))

        values = list(lengths.values())
        if values.count(values[0]) != len(values):
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
            self, "date_filed_is_approximate", [False for _ in self.case_names]
        )

        sanity_check_dates(
            zip(self.case_dates, self.case_names, date_filed_is_approximate),
            self.court_id,
        )

        logger.info(
            "%s: Successfully found %s items."
            % (self.court_id, len(self.case_names))
        )

    def _date_sort(self):
        """Sort the object by date."""
        if len(self.case_names) > 0:
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

    def _make_hash(self):
        """Make a unique ID. ETag and Last-Modified from courts cannot be
        trusted
        """
        self.hash = hashlib.sha1(str(self.case_names).encode()).hexdigest()

    def _make_html_tree(self, text):
        """Hook for custom HTML parsers

        By default, the etree.html parser is used, but this allows support for
        other parsers like the html5parser or even BeautifulSoup, if it's called
        for (example: return get_html5_parsed_text(text)). Otherwise, this method
        can be overwritten to execute custom parsing logic.
        """
        return get_html_parsed_text(text)

    async def _download(self, request_dict=None):
        """Download the latest version of Site"""
        if request_dict is None:
            request_dict = {}
        self.downloader_executed = True
        if self.method == "POST":
            truncated_params = {}
            for k, v in self.parameters.items():
                truncated_params[k] = trunc(v, 50, ellipsis="...[truncated]")
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

    def _download_content_urllib(self, download_url: str, headers: dict):
        """Download content using urllib to bypass Cloudflare

        Uses urllib instead of httpx because Cloudflare blocks httpx
        via TLS fingerprinting. Used by scrapers with `use_urllib = True`.

        :param download_url: The URL for the item you wish to download.
        :param headers: headers dict
        :return: A response object with a `content` field
        """
        req = urllib.request.Request(download_url, headers=headers)
        response = self.urllib_opener.open(req, timeout=90)
        response.content = response.read()

        return response

    async def download_content(
        self,
        download_url: str,
        doctor_is_available: bool = True,
        media_root: str = "",
    ) -> Union[str, bytes]:
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
            def handler(request: httpx.Request):
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
            s = httpx.AsyncClient(transport=transport)
            r = await s.get(url=self.url)
            return self.cleanup_content(r.content)

        if self.needs_special_headers:
            headers = self.request["headers"]
        else:
            headers = {"User-Agent": "CourtListener"}

        if self.use_urllib:
            r = self._download_content_urllib(download_url, headers)
        else:
            s = self.request["session"]
            # Note that we do a GET even if self.method is POST. This is
            # deliberate.
            r = await s.get(
                download_url,
                headers=headers,
                cookies=self.cookies,
                timeout=300,
            )

        check_empty_downloaded_file(r, download_url)
        check_expected_content_types(self, r, download_url)

        if doctor_is_available and not self.use_urllib:
            # test for and follow meta redirects, uses doctor get_extension
            # service
            r = await follow_redirections(r, s)
            r.raise_for_status()

        content = self.cleanup_content(r.content)

        return content

    def _process_html(self):
        """Hook for processing available self.html after it's been downloaded.
        This step is completely optional, but is useful if you want to transform
        the html before running the data getters (_get_*), or if its easier to
        extract the cases form the html in a linear function (here) as opposed
        to using separate data getters.  See sc.py for example.
        """
        pass

    def _process_request_parameters(self, parameters=None):
        """Hook for processing injected parameter overrides"""
        if parameters is None:
            parameters = {}
        self.request["parameters"].update(parameters)

    def _download_urllib(self):
        """Handle download using urllib backend.

        :return: parsed HTML tree or JSON object
        """
        data = None
        if self.method == "POST":
            data = urllib.parse.urlencode(self.parameters).encode("utf-8")

        raw = self._urllib_fetch(self.url, data=data)
        text = raw.decode("utf-8")

        content_type = ""
        if hasattr(self.request["response"], "getheader"):
            content_type = self.request["response"].getheader(
                "Content-Type", ""
            )
        if "json" in content_type:
            return json.loads(text)

        text = self._clean_text(text)
        html_tree = self._make_html_tree(text)
        return html_tree

    def _urllib_fetch(self, url, data=None, headers=None):
        """Fetch a URL using urllib to bypass Cloudflare TLS fingerprinting.

        httpx gets blocked by Cloudflare due to its TLS fingerprint
        (httpcore). Python's stdlib urllib uses a different TLS stack
        that Cloudflare does not block.

        :param url: URL to fetch
        :param data: POST data as bytes, or None for GET
        :param headers: optional dict of headers to use instead of defaults
        :return: raw response bytes
        """
        if headers is None:
            headers = dict(self.request["headers"])
        req = urllib.request.Request(url, data=data, headers=headers)
        response = self.urllib_opener.open(req, timeout=60)
        raw = response.read()
        # Gzip decompression - currently only needed for lactapp_3
        # whose server returns gzip-encoded responses
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)

        # Populate request dict for save_response compatibility.
        # Currently only needed for lactapp_3 which uses urllib
        self.request["url"] = url
        self.request["response"] = response
        if self.save_response:
            response.text = raw.decode("utf-8")
            response.content = raw
            response.history = []
            self.save_response(self)

        return raw

    async def _request_url_get(self, url):
        """Execute GET request and assign appropriate request dictionary
        values
        """
        self.request["url"] = url
        self.request["response"] = await self.request["session"].get(
            url,
            headers=self.request["headers"],
            timeout=60,
            **self.request["parameters"],
        )
        if self.save_response:
            self.save_response(self)

    async def _request_url_post(self, url):
        """Execute POST request and assign appropriate request dictionary values"""
        self.request["url"] = url
        self.request["response"] = await self.request["session"].post(
            url,
            headers=self.request["headers"],
            data=self.parameters,
            timeout=60,
            **self.request["parameters"],
        )
        if self.save_response:
            self.save_response(self)

    async def _request_url_mock(self, url):
        """Execute mock request, used for testing"""
        self.request["url"] = url

        def handler(request: httpx.Request):
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
        mock_client = httpx.AsyncClient(transport=transport)
        self.request["response"] = await mock_client.get(url=self.url)
        return self.request["response"]

    def _post_process_response(self):
        """Cleanup to response object"""
        self.tweak_response_object()
        self.request["response"].raise_for_status()
        set_response_encoding(self.request["response"])

    def _return_response_text_object(self):
        if self.request["response"]:
            if "json" in self.request["response"].headers.get(
                "content-type", ""
            ):
                return self.request["response"].json()
            else:
                try:
                    payload = self.request["response"].content.decode("utf8")
                except Exception:
                    payload = self.request["response"].text

                text = self._clean_text(payload)
                html_tree = self._make_html_tree(text)
                if hasattr(html_tree, "rewrite_links"):
                    html_tree.rewrite_links(
                        fix_links_in_lxml_tree, base_href=self.request["url"]
                    )
                return html_tree

    async def _get_html_tree_by_url(self, url, parameters=None):
        if parameters is None:
            parameters = {}
        self._process_request_parameters(parameters)
        await self._request_url_get(url)
        self._post_process_response()
        tree = self._return_response_text_object()
        tree.make_links_absolute(url)
        return tree

    async def _download_backwards(self, d):
        # methods for downloading the entire Site
        pass

    def make_backscrape_iterable(self, kwargs: dict) -> None:
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
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")
        days_interval = kwargs.get("days_interval")

        if start:
            start = datetime.strptime(start, "%Y/%m/%d").date()
        else:
            if hasattr(self, "first_opinion_date"):
                start = self.first_opinion_date
            else:
                logger.warning(
                    "No `backscrape_start` argument passed; and scraper has no `first_opinion_date` default"
                )

        if end:
            end = datetime.strptime(end, "%Y/%m/%d").date()
        else:
            end = datetime.now().date()

        if not days_interval:
            if hasattr(self, "days_interval"):
                days_interval = self.days_interval
            else:
                logger.warning(
                    "No `days_interval` argument passed; and scraper has no default"
                )

        self.back_scrape_iterable = make_date_range_tuples(
            start, end, days_interval
        )

    @staticmethod
    def cleanup_content(content):
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

    def _get_cookies(self):
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
        return self._cookies

    def _get_case_name_shorts(self):
        """Generates short case names for all the case names that we scrape."""
        case_name_shorts = []
        for case_name in self.case_names:
            case_name_shorts.append(self.cnt.make_case_name_short(case_name))
        return case_name_shorts

    def _get_blocked_statuses(self):
        """Should these items be blocked by search engines? Default is False for
        all subclasses, indicating that the items should not be blocked.

        This method is important because some courts (like family or asylum
        courts) should choose privacy over openness. Note that we consider
        these functions to be a hint to callers, so following these guidelines
        is not guaranteed.
        """
        return [False] * len(self.case_names)
