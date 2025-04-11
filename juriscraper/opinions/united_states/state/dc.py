"""Scraper for the D.C. Court of Appeals
CourtID: dc
Court Short Name: D.C.
Author: V. David Zvenyach
Date created:2014-02-21
"""
import re
from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlencode, urljoin
from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.baseurl = "https://www.dccourts.gov/court-of-appeals/opinions-memorandum-of-judgments"
        self.page=0
        self.status = "Published"

    def _process_html(self) -> None:
        for row in self.html.xpath(".//table[@class='table table-bordered table-condensed table-hover table-striped']//tbody/tr"):
            # docket = row.xpath(".//td[1]/a/text()")[0]
            # url=row.xpath(".//td[1]//a/@href")[0]
            td_element = row.xpath(".//td[1]")[0]

            anchor_tag = td_element.xpath(".//a")

            if anchor_tag:
                docket = anchor_tag[0].xpath("text()")[0]
                url = anchor_tag[0].xpath("@href")[0]
            else:
                docket = row.xpath(".//td[1]/text()")[0].strip()
                url = "null"
            name = row.xpath(".//td[2]/text()")[0]
            jud = row.xpath(".//td[5]/text()")[0].strip()
            if jud == 'Per Curiam':
                judge = ""
            else:
                judge = jud

            date_str = row.xpath(".//td[3]/text()")[0].strip()

            result = re.split(r'[,&]\s*', docket)

            disposition = row.xpath(".//td[4]/text()")[0].strip()

            cleaned_list = [item.strip() for item in result]
            self.cases.append(
                {
                    "date": date_str,
                    "url": url,
                    "name": name.strip(),
                    "docket": cleaned_list,
                    "judge":judge,
                    "disposition":disposition
                }
            )

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:

        if not start:
            start = datetime.today() - timedelta(days=15)
            end = datetime.today()

        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")
        params = {
            "field_date_value": start,
            "field_date_value_1": end,
            "page": self.page,
            # "Submit": "Search",
        }
        self.url = f"{self.baseurl}?{urlencode(params)}"

    def _download_backwards(self, dates: Tuple[date]) -> None:
        logger.info("Backscraping for range %s %s", *dates)
        while True:
            self.set_url(*dates)
            self.html = self._download()
            cases_before = len(self.cases)
            self._process_html()
            cases_after = len(self.cases)
            if cases_after == cases_before:
                logger.info("No more cases found. Stopping pagination.")
                break

            self.page += 1

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        print(f"start date is {start_date} and end date is {end_date}")
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
        return 0

    def get_class_name(self):
        return "dc"

    def get_court_name(self):
        return "District of Columbia Court of Appeals"

    def get_state_name(self):
        return "District Of Columbia"

    def get_court_type(self):
        return "state"
