"""Resources for scraping SCOTUS docket numbers from court documents.

> Paper remains the official form of filing at the Supreme Court.
<https://www.supremecourt.gov/filingandrules/electronicfiling.aspx>

Perhaps because of this second-millennium record keeping practice, there is no 
publicly-available digital central index of Supreme Court cases. If SCOTUS docket 
information is not obtained by attempting to query docket numbers in sequence, 
one of the Court's information sources needs to be consulted.

In descending order of relevance to scraping, these are:

[Orders of the Court](https://www.supremecourt.gov/orders/ordersofthecourt/)
[Docket Search](https://www.supremecourt.gov/docket/docket.aspx)
[Journal of the SCOTUS](https://www.supremecourt.gov/orders/journal.aspx)

**Orders of the Court**
* PDFs listing docket numbers of cases for which there has been an action. 
> Regularly scheduled lists of orders are issued on each Monday that the Court 
sits, but 'miscellaneous' orders may be issued in individual cases at any time. 
Scheduled order lists are posted on this Website on the day of their issuance, 
while miscellaneous orders are posted on the day of issuance or the next day."

**Docket Search**
* Full-text search portal that attempts to match the input string to any text 
in any docket.
* Returns URLs of the HTML rendering for dockets. From these, docket numbers can
be parsed and substituted into the URL pattern for dockets' JSON rendering.
* Passing date strings formatted like docket entry dates (e.g. 'Feb 29, 2024') 
will with high probability return a link to a docket with an entry(s) matching 
the input string.
* There appears to be a limit of 500 search results. Because some of the results 
will be for matches in the text of a docket entry rather than the entry date 
itself, it is possible that some search results will not be exhaustive.

**Journal of the Supreme Court**
* The exhaustive -- but not at all timely -- PDFs containing all docket numbers.
> The Journal of the Supreme Court of the United States contains the official 
minutes of the Court. It is published chronologically for each day the Court 
issues orders or opinions or holds oral argument. The Journal reflects the 
disposition of each case, names the court whose judgment is under review, lists 
the cases argued that day and the attorneys who presented oral argument[].
"""
from datetime import date, timedelta
from io import BytesIO

from random import shuffle
import re
from time import sleep

import fitz  # the package name of the `pymupdf` library
from lxml import html
import requests

from juriscraper.lib.log_tools import make_default_logger
from .clients import (
    download_client,
    response_handler,
    is_not_found_page,
    is_stale_content,
    jitter,
    HEADERS,
    random_ua,
)
from . import utils

logger = make_default_logger()

order_url_date_regex = re.compile(r"(\d{2})(\d{2})(\d{2})(zr|zor)")
fedrules_regex = re.compile(r"(?<=\/)(?<=\/)fr\w\w\d\d")


class SCOTUSOrders:
    """Download and parse 'Orders of the Court' PDF documents for a single term.

    These Orders include the following types of court action:

    * Certiorari -- Summary Dispositions
    * Certiorari Granted
    * Certiorari Denied
    * Statements of Justices [accompanying denial/grant of certiorari]

    The Orders *do not* include dispositions for which an Opinion is published.

    We ignore Federal Rules of judicial procedure (28 USC §2072) amendments that
    are periocially released as Orders but are not relevant here. These PDFs
    follow a file naming convention that begins with 'fr', unlike case-related
    Orders whose filenames start with six characters for MMDDYY and then
    either 'zor' for a regular Orders List or 'zr' for a Miscellaneous Order.
    """

    def __init__(
        self,
        term: int,
        *,
        session: requests.Session = None,
        cache_pdfs: bool = True,
        **kwargs,
    ):
        """Will instantiate a Session if none is passed."""
        self.term = term
        self._session = session
        self.homepage_response = None
        self.cache_pdfs = cache_pdfs
        self.order_meta = None
        self._pdf_cache = set()
        self._docket_numbers = set()

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(HEADERS)
            logger.debug(f"{self} instantiated new Session")
        return self._session

    def __del__(self):
        if self._session:
            try:
                self._session.close()
            finally:
                pass

    def orders_page_download(
        self,
        since_timestamp: str = None,
        **kwargs,
    ) -> None:
        """Download the Orders page from a single US Supreme Court term.

        Note:
            kwargs passed to session.get().
        """
        if isinstance(self.term, int):
            yy_term = str(self.term)[-2:]
        url = f"https://www.supremecourt.gov/orders/ordersofthecourt/{yy_term}"

        response = download_client(
            url=url,
            since_timestamp=since_timestamp,
            **kwargs,
        )
        # allow 304 reponses; those will be managed
        self.homepage_response = response_handler(response)

    @staticmethod
    def orders_link_parser(html_string: str) -> list:
        """Take an HTML string from the Orders page and return a list of Order URLs."""
        root = html.document_fromstring(html_string)
        url_xpath = '//*[@id="pagemaindiv"]//a[contains(@href, "courtorders")]'
        pdf_link_elements = root.xpath(url_xpath)

        link_matches = []
        for x in pdf_link_elements:
            url = f"https://www.supremecourt.gov{x.get('href')}"
            # order_type = x.text
            link_matches.append(url)
        return link_matches

    def parse_orders_page(self) -> None:
        """Extract URLs for individual order documents. Append to self.order_meta
        with Order date and order type of 'zor' (order list) or 'zr' (misc. order).
        """
        if self.homepage_response is None:
            self.orders_page_download()

        logger.debug(f"Parsing orders page for {self.term} term...")
        try:
            order_urls = self.orders_link_parser(self.homepage_response.text)
        except Exception as e:
            logger.error(
                f"orders_link_parser {self.term} raised {repr(e)}", exc_info=e
            )
            raise
        else:
            logger.info(
                f"Order PDF count for term {self.term}: {len(order_urls)}"
            )

        # extract metadata for each order list from the URL
        self.order_meta = []

        for url in order_urls:
            container = {}
            try:
                _mm, _dd, _yy, listype = order_url_date_regex.search(
                    url
                ).groups()
            except AttributeError as ae:
                if fedrules_regex.search(url):
                    # Order is an update to the federal judicial rules; ignore
                    logger.debug(f"Ignoring judicial rules update {url}")
                else:
                    logger.error(
                        f"order_url_date_regex {self.term} failed on {url}",
                        exc_info=ae,
                    )
                continue
            except TypeError as e2:
                logger.error(
                    f"URL parsing error {self.term} on {url}", exc_info=e2
                )
                continue
            else:
                container["order_date"] = date(
                    int("20" + _yy), int(_mm), int(_dd)
                )
                container["order_type"] = listype
                container["url"] = url
                self.order_meta.append(container)

    def order_pdf_download(
        self,
        url: str,
        since_timestamp: str = None,
        **kwargs,
    ) -> requests.Response:
        """Download an Orders PDF.

        Note: kwargs passed to session.get().
        """
        pdf_headers = {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Host": "www.supremecourt.gov",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-GPC": "1",
        }

        response = download_client(
            url=url,
            since_timestamp=since_timestamp,
            headers=pdf_headers,
            **kwargs,
        )
        # allow caller to handle status code 304 responses
        return response_handler(response)

    @staticmethod
    def order_pdf_parser(pdf: bytes) -> set:
        """Extract docket numbers from an Orders PDF. In-memory objects are passed to
        the 'stream' argument."""
        if isinstance(pdf, BytesIO):
            open_kwds = dict(stream=pdf)
        elif isinstance(pdf, bytes):
            open_kwds = dict(stream=BytesIO(pdf))
        else:
            open_kwds = dict(filename=pdf)

        _pdf = fitz.open(**open_kwds)
        pdf_string = "\n".join([pg.get_text() for pg in _pdf])
        matches = utils.orders_docket_regex.findall(pdf_string)
        # clean up dash characters so only U+002D is used
        docket_set = set(
            [utils.dash_regex.sub("\u002d", dn) for dn in matches]
        )
        return docket_set

    def _term_constraints(self, *, earliest: str, latest: str) -> dict:
        """Allow for more targeted Order searches within a single SCOTUS term.
        Terms run October-September."""

        earliest = utils.makedate(earliest).date() if earliest else None
        latest = utils.makedate(latest).date() if latest else None
        term_beg = utils.first_monday_oct(self.term)
        term_end = utils.first_monday_oct(self.term + 1) - timedelta(days=1)

        # handle earliest-latest transposition
        if (earliest and latest) and (earliest > latest):
            logger.debug(
                f"`earliest` {earliest} must be less than `latest` {latest}; "
                "switching their input order"
            )
            _start = earliest
            _stop = latest
        else:
            # searches run in descending chronological order
            _stop = earliest
            _start = latest

        # apply constraints
        if _start:
            _start = min(_start, term_end)
        if _stop:
            _stop = max(_stop, term_beg)
        return {"earliest": _stop, "latest": _start}

    def docket_numbers(
        self,
        earliest: date = None,
        latest: date = None,
        include_misc: bool = True,
        **kwargs,
    ) -> list:
        """Return a sorted list representation of the scraped docket number set."""
        if self._docket_numbers == set():
            self._get_orders(
                earliest=earliest, latest=latest, include_misc=include_misc
            )
        return sorted(self._docket_numbers, key=utils.docket_priority)

    def _get_orders(
        self,
        earliest: date,
        latest: date,
        include_misc: bool,
        delay: float = 0.1,
        **kwargs,
    ) -> None:
        """Find available Orders published for a given court term, extract their
        metadata and save to database.

        :param earliest: Date object or string for the earliest order date to download.
        :param latest: Date object or string for the most recent order date to download.
        :param include_misc: False to exclude miscellaneous orders; this feature
            intended for debugging use, e.g. to validate free text searches against a
            specific order list.
        """
        available_terms = set(range(2016, utils.current_term() + 1))
        if self.term not in available_terms:
            errmsg = "Only these terms available for scraping: {}"
            logger.error(
                f"Bad term {self.term} passed to orders_scraping_manager"
            )
            raise ValueError(errmsg.format(available_terms))

        # contstrain search dates to the indicated term
        date_constraints = self._term_constraints(
            earliest=earliest, latest=latest
        )
        earliest = date_constraints["earliest"]
        latest = date_constraints["latest"]
        logger.debug(
            "Scraping docket numbers from Orders: "
            f"{dict(latest=latest, earliest=earliest, misc_orders=include_misc)}"
        )

        # find Orders for this term
        self.orders_page_download(**kwargs)

        # extract Orders PDF URLs
        self.parse_orders_page()

        # download PDFs
        for meta_record in self.order_meta:
            # skip Miscellaneous Orders if `include_misc` is False
            if not include_misc and meta_record["order_type"] == "zr":
                continue

            # enforce date constraints if they were passed
            if (earliest and meta_record["order_date"] < earliest) or (
                latest and meta_record["order_date"] > latest
            ):
                continue

            url = meta_record["url"]
            pdf_response = self.order_pdf_download(url, **kwargs)

            if is_stale_content(pdf_response):
                # Got status code 304
                logger.debug(f"{url} returned status code 304; skipping ahead")
                continue
            else:
                if self.cache_pdfs:
                    self._pdf_cache.add(pdf_response)

                # parse out docket numbers
                if is_not_found_page(pdf_response):
                    logger.info(f"{url} is stale; skipping")
                    continue

                try:
                    docket_numbers = self.order_pdf_parser(
                        BytesIO(pdf_response.content)
                    )
                except Exception as e:
                    if "code=2: no objects found" in repr(e):
                        # bad URL; log and skip
                        logger.info(f"{url} is stale; skipping")
                    else:
                        logger.error(
                            f"PDF parser error {self.term} on {url}",
                            exc_info=e,
                        )
                        logger.debug(str(pdf_response.request.headers))
                        logger.debug(str(pdf_response.headers))
                        logger.debug(str(pdf_response.content[:100]))
                    if self.cache_pdfs:
                        continue
                    else:
                        raise
                else:
                    # perform set update
                    self._docket_numbers.update(docket_numbers)
                    logger.info(
                        f'Scraped {len(docket_numbers)} dockets from {meta_record["order_date"]} {meta_record["order_type"]}'
                    )
            sleep(delay + jitter(delay))


class DocketFullTextSearch:
    """Wrapper for SCOTUS 'Docket Search' feature. Search on a single string.
    <https://www.supremecourt.gov/docket/docket.aspx>"""

    SEARCH_URL = "https://www.supremecourt.gov/docket/docket.aspx"

    static_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "www.supremecourt.gov",
        "Origin": "https://www.supremecourt.gov",
        "Referer": "https://www.supremecourt.gov/docket/docket.aspx",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Sec-GPC": "1",
        "TE": "trailers",
        "User-Agent": random_ua(),
    }

    post_template = {
        "ctl00_ctl00_RadScriptManager1_TSM": "",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": None,
        "__VIEWSTATEGENERATOR": None,
        "ctl00$ctl00$txtSearch": "",
        "ctl00$ctl00$txbhidden": "",
        "ct": "Supreme-Court-Dockets",
        "ctl00$ctl00$MainEditable$mainContent$txtQuery": None,
        "ctl00$ctl00$MainEditable$mainContent$cmdSearch": "Search",
    }

    viewstate_regex = re.compile(r"(?<=__VIEWSTATE\|).*?(?=\|)")
    pagination_regex = re.compile(r"(\d+?)(?= items).*?(\d+) of (\d+)")
    result_count_regex = re.compile(r"\d+?(?= items)")

    def __init__(self, search_string: str, session=None, delay=0.5):
        """Although any search string can be passed, it will not be validated.
        Use the `date_query` classmethod to instantiate this class as intended.
        """
        self.search_string = search_string
        self.session = session or requests.Session()
        self.delay = delay
        self.search_home = None
        self.query_responses = []
        self._matching_dockets = set()

        # set default request headers
        self.session.headers.update(self.static_headers)

    def __del__(self):
        if self.session:
            self.session.close()

    @classmethod
    def date_query(cls, date_string, **kwargs):
        """Take a parsable date string (e.g. YYYY-MM-DD) and instantiate with a string
        representation that will match docket entry dates in free-text search.
        """
        output_fmt = "%b %d, %Y"
        date_obj = utils.makedate(date_string)
        date_string = date_obj.strftime(output_fmt)
        return cls(search_string=date_string, **kwargs)

    @staticmethod
    def search_page_metadata_parser(html_string):
        """Take an HTML string from the docket search web page and return
        metadata required to perform searches.
        """
        root = html.document_fromstring(html_string)

        hiddens = './/div[@class="aspNetHidden"]'
        meta_elements = {
            tag.name: tag.value for el in root.findall(hiddens) for tag in el
        }
        return meta_elements

    @staticmethod
    def _viewstate_parser(html_string):
        """Take an HTML string from the docket search web page and return
        metadata required to perform searches.
        """
        root = html.document_fromstring(html_string)

        viewstate = './/*[@id="__VIEWSTATE"]'
        meta_elements = {tag.name: tag.value for tag in root.xpath(viewstate)}
        return meta_elements

    def page_count_parser(self, html_string):
        """Take an HTML string from the docket search results. Return
        current and max `page` numbers; if missing, page count is 1.
        """
        root = html.document_fromstring(html_string)

        page_row = (
            './/*[@id="ctl00_ctl00_MainEditable_mainContent_lblCurrentPage"]'
        )
        element_text = root.xpath(page_row)[0].text

        # test for a single result page
        if page_match := self.pagination_regex.search(element_text):
            page_vals = page_match.groups()
        elif page_match := self.result_count_regex.search(element_text):
            page_vals = (page_match.group(0), 1, 1)
        else:
            raise ValueError(f"page_count_parser did not match {element_text}")
        return {
            k: int(v) for k, v in zip(("items", "cur_pg", "max_pg"), page_vals)
        }

    def full_text_search_page(self, **kwargs):
        """Download <https://www.supremecourt.gov/docket/docket.aspx> to scrape
        hidden metadata. All `kwargs` are passed to the requests client.
        """
        try:
            response = download_client(
                self.SEARCH_URL, session=self.session, **kwargs
            )
        except Exception:
            raise
        else:
            return response

    def search_query(self):
        """Send POST full text search query."""
        home_page_response = self.full_text_search_page()
        hidden_payload = self.search_page_metadata_parser(
            home_page_response.text
        )
        _search_string = self.search_string  # .replace(" ", "+")

        payload = self.post_template | hidden_payload
        payload["ctl00$ctl00$MainEditable$mainContent$txtQuery"] = (
            _search_string
        )

        try:
            _response = self.session.post(self.SEARCH_URL, data=payload)
            response = response_handler(_response)
        except Exception:
            raise
        else:
            if self.query_responses != []:
                self.query_responses.clear()
            self.query_responses.append(response)

    def pager(self):
        """Download 2,...,n pages of search results"""
        assert (
            len(self.query_responses) > 0
        ), "`search_query` must have been run first."

        header_updates = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "X-MicrosoftAjax": "Delta=true",
            "X-Requested-With": "XMLHttpRequest",
        }
        payload_updates = {
            "ctl00$ctl00$RadScriptManager1": (
                "ctl00$ctl00$MainEditable$mainContent$UpdatePanel1"
                "|ctl00$ctl00$MainEditable$mainContent$cmdNext"
            ),
            "__EVENTTARGET": "ctl00$ctl00$MainEditable$mainContent$cmdNext",
            "__EVENTARGUMENT": "",
            "ctl00$ctl00$MainEditable$mainContent$txtQuery": self.search_string,
            "__ASYNCPOST": True,
            "": "",
        }
        hidden_payload = self.search_page_metadata_parser(
            self.query_responses[0].text
        )

        payload = self.post_template.copy()
        # must delete the following key for paging to work
        # https://toddhayton.com/2015/05/04/scraping-aspnet-pages-with-ajax-pagination/
        del payload["ctl00$ctl00$MainEditable$mainContent$cmdSearch"]

        # now update POST payload
        payload.update(hidden_payload)
        payload.update(payload_updates)
        payload["ctl00$ctl00$MainEditable$mainContent$txtQuery"] = (
            self.search_string
        )
        # extract __VIEWSTATE value from non-HTML text
        if vs_match := self.viewstate_regex.search(
            self.query_responses[-1].text
        ):
            payload["__VIEWSTATE"] = vs_match.group(0)

        try:
            response = self.session.post(
                self.SEARCH_URL, data=payload, headers=header_updates
            )
        except Exception:
            raise
        else:
            self.query_responses.append(response)

    def scrape(self):
        """Execute a search query and page through the results."""
        self.search_query()

        try:
            result_params = self.page_count_parser(
                self.query_responses[0].text
            )
        except AttributeError as ae:
            if "NoneType" in repr(ae):
                errmsg = (
                    "Failed to find page count response in search on "
                    f"{self.search_string}"
                )
                logger.error(errmsg, exc_info=ae)
                logger.debug(
                    f"Payload: {self.query_responses[0].request.body}"
                )
                raise
        except Exception as e:
            errmsg = f".scrape on {self.search_string} raised {repr(e)}"
            logger.error(errmsg, exc_info=e)
            logger.debug(self.query_responses[0].request.headers)
            logger.debug(self.query_responses[0].headers)
            logger.debug(f"Payload: {self.query_responses[0].request.body}")
            logger.debug(f".text: {self.query_responses[0].text[:300]}")
            logger.debug(self.query_responses[0].text[3000:5000])
            raise

        logger.debug(
            f"'{self.search_string}' first page results {result_params}"
        )
        iter_count = result_params["max_pg"]
        current_page = result_params["cur_pg"]

        while current_page < iter_count:
            sleep(self.delay)
            try:
                self.pager()
            except Exception as e:
                logger.error(f"current page {current_page}", exc_info=e)
                raise

            try:
                result_params = self.page_count_parser(
                    self.query_responses[-1].text
                )
            except IndexError as ie:
                logger.debug(self.query_responses[-1].request.headers)
                logger.debug(self.query_responses[-1].headers)
                logger.debug(self.query_responses[-1].text)
                logger.error(
                    f"Current pg: {current_page} iter_count: {iter_count}",
                    exc_info=ie,
                )
            except Exception as e:
                logger.error(f"current page {current_page}", exc_info=e)
                raise
            else:
                current_page = result_params["cur_pg"]

    @staticmethod
    def docket_number_parser(html_string):
        """Take an HTML string from the docket search results and return
        a list of docket numbers.
        """
        root = html.document_fromstring(html_string)
        url_xpath = '//a[contains(@href, "docketfiles")]'
        pdf_link_elements = root.xpath(url_xpath)

        link_matches = []
        for x in pdf_link_elements:
            if matched := utils.docket_number_regex.search(x.text):
                corrected = utils.dash_regex.sub("\u002d", matched.group(0))
                link_matches.append(utils.endocket(corrected))
        return set(link_matches)

    def parse_dockets(self):
        """Parse docket numbers out of search results."""
        assert self.query_responses != []

        for r in self.query_responses:
            try:
                docketnums = self.docket_number_parser(r.text)
            except Exception as e:
                logger.debug(r.text[5000:7000], exc_info=e)
                raise
            else:
                self._matching_dockets.update(docketnums)

    @property
    def matching_dockets(self):
        """Return a sorted list of docket numbers."""
        if not self._matching_dockets:
            self.scrape()
            self.parse_dockets()
        return sorted(self._matching_dockets, key=utils.docket_priority)

    def randomized_dockets(self):
        """Return a randomized list of discovered docket numbers."""
        sd = self.matching_dockets
        shuffle(sd)
        return sd
