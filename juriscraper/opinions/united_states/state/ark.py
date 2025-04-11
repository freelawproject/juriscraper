# Author: Phil Ardery
# Date created: 2017-01-27
# Contact: 501-682-9400 (Administrative Office of the Curt)

import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from dns.name import empty
from lxml import html
import \
    requests

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.string_utils import normalize_dashes, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_code = "144"
    cite_regex = re.compile(r"\d{2,4} Ark\. \d+", re.IGNORECASE)
    first_opinion_date = datetime(1979, 9, 3)
    days_interval = 7
    not_a_opinion_regex = r"SYLLABUS|(NO (COURT OF APPEALS )?OPINION)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flag=True
        self.court_id = self.__module__
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        # Empty document
        h1=list(self.html.xpath("//h1"))
        if h1.__len__()!=0:
            h1_text=h1[0].text
            if h1_text.__eq__('Empty document'):
                self.flag=False
                return
        rows = self.html.xpath("//div[@class='info']")
        if len(rows) >= 25:
            logger.info("25 results for this query, results may be lost in pagination")
        for item in rows:
            per_curiam = False
            name = item.xpath(".//a/text()")[0]
            url = item.xpath(".//a/@href")[1]
            if re.search(self.not_a_opinion_regex, name.upper()):
                logger.info("Skipping %s %s, invalid document", name, url)
                continue

            cite = item.xpath(".//*[@class='citation']/text()")
            docket_url = item.xpath(".//a/@href")[0]+"?iframe=true"
            response = requests.get(url=docket_url, headers={"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"}, proxies={"http": "p.webshare.io:9999", "https": "p.webshare.io:9999"}, timeout=120)
            html_tree = self._make_html_tree(response.text)
            docket=[]
            docket_data = html_tree.xpath("//tr[td[@class='label' and text()='Docket Number']]/td[@class='metadata']/text()")
            if list(docket_data).__len__()!=0:
                docket.append(docket_data[0].strip())

            if cite:
                cite = cite[0]

            if metadata := item.xpath(".//*[@class='subMetadata']/span[2]"):
                per_curiam = metadata[0].text_content().strip() == "Per Curiam"

            date_filed = item.xpath(".//*[@class='publicationDate']/text()")[0]
            if self.cases.__contains__({"date": date_filed, "docket": [], "name": titlecase(name), "citation": [cite], "url": url, "status": "Published", "per_curiam": per_curiam}):
                return
            self.cases.append(
                {
                    "date": date_filed,
                    "docket": docket,
                    "name": titlecase(name),
                    "citation": [cite],
                    "url": url,
                    "status": "Published",
                    "per_curiam": per_curiam,
                    "html_url":docket_url,
                    "response_html":response.text

                }
            )

    def set_url(self, start_date, end_date, base_url) -> None:
        # if not start_date:
        #     end = datetime.now() + timedelta(1)
        #     start = end - timedelta(7)
        params = {
            "cont": "",
            "ref": "",
            "d1": start_date.strftime("%m/%d/%Y"),
            "d2": end_date.strftime("%m/%d/%Y"),
            "col": self.court_code,
            "tf1": "",
            "tf2": "",
            "or": "date",
            "iframe": "true",
        }
        self.url = f"{base_url}?{urlencode(params)}"

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: metadata
        """
        normalized_content = normalize_dashes(scraped_text)
        match = re.findall(r"No\. (\w+-\d+-\d+)", normalized_content)
        if match:
            return {"OpinionCluster": {"docket_number": match[0]}}
        return {}

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request
        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = self._download()
        self._process_html()

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        i=1
        while self.flag:
            base_url = f"https://opinions.arcourts.gov/ark/en/d/s/{i}/infiniteScroll.do"
            self.set_url(start_date,end_date,base_url)
            self.parse()
            if not self.flag:
                break
            i = i + 1
            self.downloader_executed=False
        return 0

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
                if(text.__eq__('')):
                    text='<!doctype html><html lang="en"><head><title>Empty</title></head><body><h1>Empty document</h1></body></html>'
                html_tree = self._make_html_tree(text)
                if hasattr(html_tree, "rewrite_links"):
                    html_tree.rewrite_links(
                        fix_links_in_lxml_tree, base_href=self.request["url"]
                    )
                return html_tree

    def get_state_name(self):
        return "Arkansas"

    def get_class_name(self):
        return "ark"

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "Supreme Court of Arkansas"
