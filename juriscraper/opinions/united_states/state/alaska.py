from datetime import date, datetime
from typing import Dict, Tuple

from dateutil import parser
import requests
from requests.exceptions import ChunkedEncodingError

from casemine.casemine_util import CasemineUtil
from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.html_utils import (get_row_column_links, get_row_column_text, )


class Site(OpinionSiteLinear):
    # Sharin S. Anderson v Alyeska Pipeline Service Co.; Opinion Number: 6496
    first_opinion_date = datetime(2010, 7, 23).date()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_backscrape = False
        self.make_backscrape_iterable(kwargs)
        self.court_id = self.__module__
        self.url = "https://appellate-records.courts.alaska.gov/CMSPublic/Home/Opinions?isCOA=False"
        self.status = "Published"
        # juriscraper in the user agent crashes it
        # it appears to be just straight up blocked.
        self.request["headers"]["user-agent"] = "Free Law Project"
        self.opinion_type ="opinion"

    def _download(self, request_dict={}):
        # Unfortunately, about 2/3 of calls are rejected by alaska but
        # if we just ignore those encoding errors we can live with it
        try:
            return super()._download(request_dict)
        except ChunkedEncodingError:
            return None

    def hit_retry(self,html_url):
        try:
            response = requests.get(url=html_url, headers={"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"}, proxies={"http": "p.webshare.io:9999", "https": "p.webshare.io:9999"}, timeout=120)
            if response.status_code==200:
                payload = response.content.decode("utf8")
                text = self._clean_text(payload)
                return text
            else:
                return "HIT AGAIN"
        except Exception as e:
            return "HIT AGAIN"

    def _process_html(self) -> None:
        if not self.html:
            logger.info("HTML was not downloaded from source page. Should retry")
            return
        for table in self.html.xpath("//table"):
            adate = table.xpath("./preceding-sibling::h5")[0].text_content()
            if self.is_backscrape and not self.date_is_in_backscrape_range(adate):
                logger.debug("Backscraper skipping %s", adate)
                continue
            for row in table.xpath(".//tr"):
                if row.text_content().strip():
                    # skip rows without PDF links in first column
                    try:
                        url = get_row_column_links(row, 1)
                        url=str(url).replace("'","%27")
                        # print(f"{adate} Main-Pdf - {url}")
                    except IndexError:
                        html_url=row.xpath('.//td[@title="Case Number and Link to the Case"]/a/@href')[0]
                        print(f"{adate} html-url - {html_url}")
                        retry_flag = True
                        text = None
                        while retry_flag:
                            text = self.hit_retry(html_url)
                            print("\n\t!! HIT AGAIN !!")
                            if not str(text).__eq__("HIT AGAIN"):
                                retry_flag=False

                        if text is not None:
                            html_tree = self._make_html_tree(text)
                            url = 'https://appellate-records.courts.alaska.gov' + html_tree.xpath("//table[@class='table cms-case-other-table table-striped']//tr//td[@title='Document Download']/a/@href")[0]
                            print(f"{adate} New-Pdf - {url}\n")

                    curr_date = datetime.strptime(adate, "%A, %B %d, %Y").strftime("%d/%m/%Y")
                    res=CasemineUtil.compare_date(self.crawled_till, curr_date)
                    if res==1:
                        return
                    if self.opinion_type.__eq__("bail orders") or self.opinion_type.__eq__("orders"):
                        docs = str(get_row_column_text(row, 2)).replace(" ","").split(",")
                        title=get_row_column_text(row, 3)
                    else:
                        docs = str(get_row_column_text(row, 3)).replace(" ","").split(",")
                        title = get_row_column_text(row, 4)
                    cite = []
                    if self.url.__eq__("https://appellate-records.courts.alaska.gov/CMSPublic/Home/Opinions?isCOA=False"):
                        cite = str(get_row_column_text(row, 5)).split(",")
                    # print(cite)

                    self.cases.append(
                        {
                            "date": adate,
                            "docket": docs,
                            "name": title,
                            "citation": cite,
                            "url": url,
                            "opinion_type":self.opinion_type
                        }
                    )

    def make_backscrape_iterable(self, kwargs: Dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        Alaska's opinions page returns all opinions, so we must only load it
        (successfully, because it may load partially) once.
        We can use the backscrape arguments to filter out opinions not in the
        date range we are looking for

        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%m/%d/%Y").date()
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y").date()
        else:
            end = datetime.now().date()

        self.back_scrape_iterable = [(start, end)]

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Called when backscraping

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.start_date, self.end_date = dates
        self.is_backscrape = True
        logger.info(
            "Backscraping for range %s %s", self.start_date, self.end_date
        )

    def date_is_in_backscrape_range(self, date_str: str) -> bool:
        """When backscraping, check if the table date is in
        the backscraping range

        :param date_str: string date from the HTML source
        :return: True if date is in backscrape range
        """
        parsed_date = parser.parse(date_str).date()
        return self.start_date <= parsed_date and parsed_date <= self.end_date

    def parse(self):
        if not self.downloader_executed:
            # Run the downloader if it hasn't been run already
            self.html = self._download()
            while self.html is None:
                self.html=self._download()
            self._process_html()

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return self

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "Supreme Court Of The State Of Alaska"

    def get_class_name(self):
        return "alaska"

    def get_state_name(self):
        return "Alaska"
