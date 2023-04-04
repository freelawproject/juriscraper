import time
from datetime import date

import certifi
import requests
from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = (
            "http://digitalcommons.law.villanova.edu/thirdcircuit_{year}/"
        )
        self.url = self.base_url.format(year=date.today().year)
        self.court_id = self.__module__
        self.back_scrape_iterable = list(range(2003, date.today().year + 1))
        self.case_xpath = "//p[@class='article-listing']/a/@href"
        self.next_page_xpath = "//div[@class='adjacent-pagination']//li[@class='active']//following-sibling::li/a/@href"

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            # Note that this is returning a list of HTML trees.
            html_trees = [
                super()._download(request_dict=request_dict),
            ]
        else:
            html_l = super()._download(request_dict)
            html_trees = self._get_case_html_page([], html_l, request_dict)

            # handle the next page data
            if html_l.xpath(self.next_page_xpath):
                self.url = html_l.xpath(self.next_page_xpath)[0]
                html_next_trees = self._download(request_dict)
                html_trees.extend(html_next_trees)
        return html_trees

    def _get_case_html_page(self, html_trees, html_l, request_dict):
        """Gets each of the individual case pages"""
        s = requests.session()
        for case_url in html_l.xpath(self.case_xpath):
            logger.info(f"  Getting sub-page at: {case_url}")
            r = s.get(
                case_url,
                headers={"User-Agent": "Juriscraper"},
                verify=certifi.where(),
                timeout=60,
                **request_dict,
            )

            r.raise_for_status()

            # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
            if r.encoding == "ISO-8859-1":
                r.encoding = "cp1252"

            # Grab the content
            text = self._clean_text(r.text)
            html_tree = html.fromstring(text)
            html_tree.make_links_absolute(self.url)

            remove_anchors = lambda url: url.split("#")[0]
            html_tree.rewrite_links(remove_anchors)
            html_trees.append(html_tree)
        return html_trees

    def _get_case_names(self):
        data = []
        for html_tree in self.html:
            try:
                data.append(html_tree.xpath("//div[@id='title']//a/text()")[0])
            except IndexError:
                data.append("")
        return data

    def _get_download_urls(self):
        data = []
        for html_tree in self.html:
            try:
                data.append(html_tree.xpath("//div[@id='title']//a/@href")[0])
            except IndexError:
                data.append("")
        return data

    def _get_case_dates(self):
        data = []
        for html_tree in self.html:
            try:
                date__ = html_tree.xpath(
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

    def _get_docket_numbers(self):
        data = []
        for html_tree in self.html:
            try:
                data.append(
                    html_tree.xpath("//div[@id='comments']//p/text()")[0]
                    .replace("No.", "")
                    .strip()
                )
            except IndexError:
                data.append("")
        return data

    def _get_precedential_statuses(self):
        data = []
        for html_tree in self.html:
            try:
                status = html_tree.xpath("//div[@id='precedent']//p/text()")[0]
                if "non" in status.lower():
                    data.append("Unpublished")
                else:
                    data.append("Published")
            except IndexError:
                data.append("Unknown")
        return data

    def _get_lower_courts(self):
        data = []
        for html_tree in self.html:
            try:
                data.append(
                    html_tree.xpath("//div[@id='abstract']//p/text()")[0]
                )
            except IndexError:
                data.append("")
        return data

    def _download_backwards(self, d):
        self.url = self.base_url.format(year=d)
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def _post_parse(self):
        """This will remove the cases without a case name"""
        to_be_removed = [
            index
            for index, case_name in enumerate(self.case_names)
            if not case_name
        ]

        for attr in self._all_attrs:
            item = getattr(self, attr)
            if item is not None:
                new_item = self.remove_elements(item, to_be_removed)
                self.__setattr__(attr, new_item)

    @staticmethod
    def remove_elements(list_, indexes_to_be_removed):
        return [
            i for j, i in enumerate(list_) if j not in indexes_to_be_removed
        ]
