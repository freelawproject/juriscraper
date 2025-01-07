import re
from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlencode, urljoin
from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    days_interval = 15
    first_opinion_date = datetime(1995, 6, 1).date()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.wicourts.gov/supreme/scopin.jsp"
        self.page = 1
        prev_len =0
        self.status = "Published"
        self.set_url()
        self.cite_regex = (
            r"(?P<volume>20\d{2})\s(?P<reporter>WI)\s(?P<page>\d+)"
        )
        self.make_backscrape_iterable(kwargs)

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Sets URL with appropriate query parameters

        :param start: start date
        :param end: end date
        :return None
        """
        if not start:
            start = datetime.today() - timedelta(days=15)
            end = datetime.today()

        start = start.strftime("%m-%d-%Y")
        end = end.strftime("%m-%d-%Y")

        params = {
            "range": "None",
            "page" : self.page,
            "begin_date": start,
            "end_date": end,
            "sortBy": "date",
            "Submit": "Search",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"

    def _process_html(self) -> None:
        """Process the HTML from wisconsin

        :return: None
        """
        for row in self.html.xpath(".//table/tbody/tr"):
            date, docket, caption, link = row.xpath("./td")
            # print(f"caption is {caption.text}")
            self.cases.append(
                {
                    "date": date.text,
                    "name": caption.text,
                    "url": urljoin(
                        "https://www.wicourts.gov",
                        link.xpath("./input")[0].name,
                    ),
                    "docket": [docket.text],
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract citation from text

        :param scraped_text: Text of scraped content
        :return: date filed
        """
        first_line = scraped_text[:100].splitlines()[0]
        match = re.search(self.cite_regex, first_line)

        if match:
            return {"Citation": {**match.groupdict(), "type": 8}}
        return {}

    def _download_backwards(self, dates: Tuple[date]) -> None:
        logger.info("Backscraping for range %s %s", *dates)
        self.prev_len = 0
        total_page=0
        while True:
            self.set_url(*dates)
            self.html = self._download()
            if self.page == 1:
                total_page = self.html.xpath(
                    ".//form[@name='frmSubmitForm']//table//table//td//strong[2]/text()")
                # print(f" {type(self.page)} and {type(total_page)}")

            self._process_html()
            if (self.page==int(total_page[0].strip())):
                break
            self.page += 1


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        print(f"crawling between range {start_date} and {end_date}")
        self._download_backwards((start_date, end_date))
        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "wis"

    def get_state_name(self):
        return "Wisconsin"

    def get_court_name(self):
        return "Supreme Court of Wisconsin"
