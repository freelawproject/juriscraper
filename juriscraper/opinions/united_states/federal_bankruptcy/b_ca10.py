"""
Scraper for the United States Bankruptcy Appellate Panel for the Tenth Circuit
CourtID: bap10
Court Short Name: 10th Cir. BAP
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-01: First draft by Jon Andersen
    2014-09-02: Revised by mlr to use _clean_text() instead of pushing logic
                into the _get_case_dates function.
"""

from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = url = "https://www.bap10.uscourts.gov/opinion/search/results"
    first_opinion_date = datetime(1996, 11, 12)
    days_interval = 120

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        for row in self.html.xpath(".//tr"):
            if not row.xpath(".//td"):
                continue


            date = row.xpath(".//td")[2].text_content().strip()
            month, day, year = date.split('/')
            case_date = f"{day}/{month}/{year}"
            self.cases.append(
                {
                    "docket": [row.xpath(".//td")[0].text_content().strip()],
                    "name": row.xpath(".//td")[1].text_content().strip(),
                    "date": date,
                    "lower_court": row.xpath(".//td")[3].text_content().strip(),
                    "url": row.xpath(".//a/@href")[0],
                    "status": "Published",
                }
            )

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        if not start:
            end = date.today()
            start = end - timedelta(30)

        params = {
            "keywords": "",
            "parties": "",
            "judges": "",
            "field_opinion_date_value[min][date]": start.strftime("%m/%d/%Y"),
            "field_opinion_date_value[max][date]": end.strftime("%m/%d/%Y"),
            "exclude": "",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"

    def _download_backwards(self, dates: Tuple[date]) -> None:
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = self._download()
        self._process_html()

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self._download_backwards((start_date,end_date))

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return 0

    def get_class_name(self):
        return "b_ca10"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "10th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court of Appeals for the Tenth Circuit"
