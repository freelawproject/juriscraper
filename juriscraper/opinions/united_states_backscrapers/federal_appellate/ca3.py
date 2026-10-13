import time
from collections.abc import Sequence
from datetime import date

from lxml import html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import RequestParameters, SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite[int]):
    status: int

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.base_url = (
            "http://digitalcommons.law.villanova.edu/thirdcircuit_{year}/"
        )
        self.url = self.base_url.format(year=date.today().year)
        self.court_id = self.__module__
        self.back_scrape_iterable = list(range(2003, date.today().year + 1))
        self.case_xpath = "//p[@class='article-listing']/a/@href"
        self.next_page_xpath = "//div[@class='adjacent-pagination']//li[@class='active']//following-sibling::li/a/@href"

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> list[HtmlElement]:
        if request_dict is None:
            request_dict = {}
        html_l = await super()._download(request_dict)
        if not isinstance(html_l, HtmlElement):
            raise TypeError("Expected an HTML case listing")
        if self.test_mode_enabled():
            # Note that this is returning a list of HTML trees.
            html_trees = [
                html_l,
            ]
        else:
            html_trees = await self._get_case_html_page(html_l, request_dict)

            # handle the next page data
            if bool(html_l.xpath(self.next_page_xpath)):
                self.url = html_l.xpath(self.next_page_xpath)[0]
                html_next_trees = await self._download(request_dict)
                html_trees.extend(html_next_trees)
        return html_trees

    async def _get_case_html_page(
        self, html_l: HtmlElement, request_dict: RequestParameters
    ) -> list[HtmlElement]:
        """Gets each of the individual case pages"""
        s = self.request["session"]
        request_dict = request_dict.copy()
        request_dict.setdefault("headers", {"User-Agent": self.user_agent})
        request_dict.setdefault("timeout", self._request_timeout)
        html_trees: list[HtmlElement] = []
        case_urls: list[str] = html_l.xpath(self.case_xpath)
        for case_url in case_urls:
            logger.info(f"  Getting sub-page at: {case_url}")
            r = await s.request(
                "GET",
                case_url,
                **request_dict,
            )

            r.raise_for_status()

            # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
            if r.encoding == "ISO-8859-1":
                r.encoding = "cp1252"

            # Grab the content
            text = self._clean_text(r.text)
            html_tree = html.fromstring(text)
            html_tree.make_links_absolute(str(r.url))

            html_tree.rewrite_links(lambda url: url.split("#")[0])
            html_trees.append(html_tree)
        return html_trees

    @override
    def _get_case_names(self) -> list[str]:
        data = []
        if not isinstance(self.html, list):
            raise TypeError("Expected downloaded HTML documents")
        for html_tree in self.html:
            if not isinstance(html_tree, HtmlElement):
                raise TypeError("Expected a downloaded HTML document")
            try:
                name: str = html_tree.xpath("//div[@id='title']//a/text()")[0]
                data.append(name)
            except IndexError:
                data.append("")
        return data

    @override
    def _get_download_urls(self) -> list[str]:
        data = []
        if not isinstance(self.html, list):
            raise TypeError("Expected downloaded HTML documents")
        for html_tree in self.html:
            if not isinstance(html_tree, HtmlElement):
                raise TypeError("Expected a downloaded HTML document")
            try:
                url: str = html_tree.xpath("//div[@id='title']//a/@href")[0]
                data.append(url)
            except IndexError:
                data.append("")
        return data

    @override
    def _get_case_dates(self) -> list[date | str]:
        data: list[date | str] = []
        if not isinstance(self.html, list):
            raise TypeError("Expected downloaded HTML documents")
        for html_tree in self.html:
            if not isinstance(html_tree, HtmlElement):
                raise TypeError("Expected a downloaded HTML document")
            try:
                date__: str = html_tree.xpath(
                    "//div[@id='publication_date']/p/text()"
                )[0]
                data.append(
                    date.fromtimestamp(
                        time.mktime(time.strptime(date__, "%m-%d-%Y"))
                    )
                )
            except IndexError:
                data.append("")
        return data

    @override
    def _get_docket_numbers(self) -> list[str]:
        data = []
        if not isinstance(self.html, list):
            raise TypeError("Expected downloaded HTML documents")
        for html_tree in self.html:
            if not isinstance(html_tree, HtmlElement):
                raise TypeError("Expected a downloaded HTML document")
            try:
                docket: str = html_tree.xpath(
                    "//div[@id='comments']//p/text()"
                )[0]
                data.append(docket.replace("No.", "").strip())
            except IndexError:
                data.append("")
        return data

    @override
    def _get_precedential_statuses(self) -> list[str]:
        data = []
        if not isinstance(self.html, list):
            raise TypeError("Expected downloaded HTML documents")
        for html_tree in self.html:
            if not isinstance(html_tree, HtmlElement):
                raise TypeError("Expected a downloaded HTML document")
            try:
                status: str = html_tree.xpath(
                    "//div[@id='precedent']//p/text()"
                )[0]
                if "non" in status.lower():
                    data.append("Unpublished")
                else:
                    data.append("Published")
            except IndexError:
                data.append("Unknown")
        return data

    @override
    def _get_lower_courts(self) -> list[str]:
        data = []
        if not isinstance(self.html, list):
            raise TypeError("Expected downloaded HTML documents")
        for html_tree in self.html:
            if not isinstance(html_tree, HtmlElement):
                raise TypeError("Expected a downloaded HTML document")
            try:
                lower_court: str = html_tree.xpath(
                    "//div[@id='abstract']//p/text()"
                )[0]
                data.append(lower_court)
            except IndexError:
                data.append("")
        return data

    @override
    async def _download_backwards(self, d: int) -> None:
        self.url = self.base_url.format(year=d)
        self.html = await self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    @override
    def _post_parse(self) -> None:
        """This will remove the cases without a case name"""
        if self.case_names is None:
            raise ValueError(
                "Case names must be populated before filtering them."
            )
        to_be_removed = [
            index
            for index, case_name in enumerate(self.case_names)
            if not bool(case_name)
        ]

        for attr in self._all_attrs:
            item: Sequence[object] | None = getattr(self, attr)
            if item is not None:
                new_item = self.remove_elements(item, to_be_removed)
                self.__setattr__(attr, new_item)

    @staticmethod
    def remove_elements(
        list_: Sequence[object], indexes_to_be_removed: Sequence[int]
    ) -> list[object]:
        return [
            i for j, i in enumerate(list_) if j not in indexes_to_be_removed
        ]
