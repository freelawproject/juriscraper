import datetime
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.string_utils import titlecase, trunc
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    """This site has an artificial limit of 50/1 minute and 100/5 minutes.

    To stay under that cap we are going to just request the first 10 opinions.  Judging on the number of opinions
    filed in each court we should be fine.

    Additionally, we moved docket number capture to PDF extraction, to limit the number of requests.
    """

    base_url = "https://nmonesource.com/nmos/en/d/s/index.do"
    court_code = "182"
    first_opinion_date = datetime(1900, 1, 1)
    days_interval = 15
    flag = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parse HTML into case dictionaries

        XMLHttpRequest pagination is triggered every 25 rows, so we must
        try to avoid big date intervals

        :return None
        """

        if self.html is None:
            return
        rows = self.html.xpath("//div[@class='info']")
        if len(rows) >= 25:
            logger.info(
                "25 results for this query, results may be lost in pagination"
            )

        for row in rows:
            url = row.xpath(
                ".//a[contains(@title, 'Download the PDF version')]/@href"
            )[0]
            name = row.xpath(".//span[@class='title']/a/text()")[0]

            # Adding html url and response_html
            html_url=row.xpath(".//span[@class='title']/a/@href")[0]
            response = requests.get(url=html_url, proxies=self.proxies, timeout=120)
            response_html = ""
            if response.status_code==200:
                response_html = response.text

            date_filed = row.xpath(".//span[@class='publicationDate']/text()")[
                0
            ]

            cite = row.xpath(".//span[@class='citation']/text()")
            citation = cite[0] if cite else ""

            status = "Unknown"
            metadata = row.xpath(".//div[@class='subMetadata']/span/text()")
            if metadata:
                status = (
                    "Published"
                    if "Reported" in metadata[-1]
                    else "Unpublished"
                )
            else:
                status = "Unknown"

            # docket no, htmlurl, html, judges
            self.cases.append(
                {
                    "date": date_filed,
                    "html_url": html_url,
                    "response_html":response_html,
                    "docket": "",
                    "name": titlecase(name),
                    "citation": citation,
                    "url": url,
                    "status": status,
                }
            )

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Formats and sets `self.url` with date inputs

        If no start or end dates are given, scrape last 7 days.

        :param start: start date
        :param end: end date

        :return None
        """
        if not start:
            end = datetime.today()
            start = datetime(2024,1,1)

        params = {
            "cont": "",
            "ref": "",
            "d1": start.strftime("%m/%d/%Y"),
            "d2": end.strftime("%m/%d/%Y"),
            "col": self.court_code,
            "rdnpv": "",
            "rdnii": "",
            "rdnct": "",
            "ca": "",
            "p": "",
            "or": "date",
            "iframe": "true",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = self._download()
        self._process_html()

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: metadata
        """
        docket_number = re.findall(r"N[oO]\.\s(.*)", scraped_text)[0]
        metadata = {
            "OpinionCluster": {
                "docket_number": docket_number,
            },
        }
        return metadata

    def _return_response_text_object(self):
        if self.request["response"]:
            if "json" in self.request["response"].headers.get(
                "content-type", ""
            ):
                return self.request["response"].json()
            else:
                try:
                    payload = self.request["response"].content.decode("utf8")
                except:
                    payload = self.request["response"].text

                text = self._clean_text(payload)
                if text.__eq__(''):
                    self.flag = False
                    return None
                else:
                    html_tree = self._make_html_tree(text)
                    if hasattr(html_tree, "rewrite_links"):
                        html_tree.rewrite_links(
                            fix_links_in_lxml_tree, base_href=self.request["url"]
                        )
                    return html_tree

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        page = 1
        sdate = start_date.strftime("%m/%d/%Y").replace("/", "%2F")
        edate = end_date.strftime("%m/%d/%Y").replace("/", "%2F")
        while self.flag:
            self.url=f'https://nmonesource.com/nmos/en/d/s/{page}/infiniteScroll.do?cont=&ref=&rdnpv=&rdnii=&rdnct=&d1={sdate}&d2={edate}&ca=&p=&col={self.court_code}&or=date&iframe=true'
            self.parse()
            self.downloader_executed=False
            page=page+1
        return 0

    def get_state_name(self):
        return "New Mexico"

    def get_class_name(self):
        return "nm"

    def get_court_name(self):
        return "Supreme Court of New Mexico"

    def get_court_type(self):
        return "state"
