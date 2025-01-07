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
        self._opt_attrs = self._opt_attrs + ["ai_summary_urls", "ai_summary_htmls"]
        self.valid_keys.update({"ai_summary_url", "ai_summary_html"})
        self._all_attrs = self._req_attrs + self._opt_attrs
        # Set all metadata to None
        for attr in self._all_attrs:
            self.__setattr__(attr, None)

    def _get_ai_summary_urls(self):
        return self._get_optional_field_by_id("ai_summary_url")

    def _get_ai_summary_htmls(self):
        return self._get_optional_field_by_id("ai_summary_html")

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
            cite = row.xpath(".//span[@class='citation']/text()")
            citation = cite[0] if cite else ""

            # Adding html url and response_html
            html_url=row.xpath(".//span[@class='title']/a/@href")[0]
            if not str(html_url).__contains__('?iframe=true'):
                html_url=f"{html_url}?iframe=true"

            print(f"\nhitting html {html_url}")
            response = requests.get(url=html_url, proxies=self.proxies, timeout=120)
            response_html = ""
            doc_list = []
            judges = ""
            ai_summary_url = ""
            ai_summary_html = ""
            jud_list=[]
            new_j_list=[]
            parallal_cite=[]
            updated_response_html = None
            if response.status_code==200:
                response_html = response.text
                soup = BeautifulSoup(response_html,'html.parser')
                meta_div = soup.find('div', id='decisia-main-content')
                updated_response_html = meta_div.prettify()
                header_div = meta_div.find('div', id="decisia-document-header")
                box_content = header_div.find('div', class_="decisia-box")
                meta_data = box_content.find('div', class_="metadata")
                table = meta_data.find('table')
                # meta_tbody = table.find_next("tbody")
                trs = table.find_all("tr")
                for tr in trs:
                    td = tr.find_all_next('td')[1]
                    if tr.text.__contains__('Parallel Citations'):
                        parallal_cite.append(td.text.strip())
                    if tr.text.__contains__('Docket Numbers'):
                        docket = td.text.replace("\n", "").replace("Docket Numbers", "").strip()
                        doc_arr=[]
                        if docket.__contains__(","):
                            doc_arr = docket.split(',')
                        if doc_arr.__len__()==0:
                            doc_list.append(docket)
                        else:
                            for doc in doc_arr:
                                doc_list.append(doc.strip())
                    if tr.text.__contains__('Decision-maker(s)'):
                        judges = td.text.replace("\n", "").replace("Decision-maker(s)", "").strip()
                        jud_list = judges.split(';')
                        for i in jud_list:
                            new_j_list.append(i.strip())
                    if tr.text.__contains__('AI generated summary'):
                        ai_summary_url = td.find_next('a').attrs.get('href')
                        if not ai_summary_url.__contains__('https://nmonesource.com/') or not ai_summary_url.__contains__('?iframe=true'):
                            ai_summary_url = 'https://nmonesource.com' + ai_summary_url
                            ai_summary_url = ai_summary_url + '?iframe=true'

                print(f'hitting ai url {ai_summary_url}')
                if not ai_summary_url.__eq__(''):
                    ai_resp = requests.get(url=ai_summary_url, proxies=self.proxies, timeout=120)
                    ai_summary_html = ai_resp.text
                    ai_soup=BeautifulSoup(ai_summary_html,'html.parser')
                    ai_summary_html = ai_soup.find('div',id="decisia-main-content").prettify()

            date_filed = row.xpath(".//span[@class='publicationDate']/text()")[0]

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
                    "response_html":updated_response_html,
                    "docket": doc_list,
                    "name": titlecase(name),
                    "citation": [citation],
                    "parallel_citation":parallal_cite,
                    "judge":new_j_list,
                    "url": url,
                    "status": status,
                    "ai_summary_url":ai_summary_url,
                    "ai_summary_html":ai_summary_html,
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
