import datetime
from datetime import date, datetime
from urllib.parse import urlencode
from typing import Optional, Tuple

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.sccourts.org/opinions-orders/opinions/published-opinions/supreme-court/"
        # self.base_url = ("https://www.sccourts.org/opinions-orders/opinions/opinion-search/")
        self.cases = []
        self.status="Published"

    def set_url(self, month, year ):
        if month<10:
            params = {
                "term": f"{year}-0{month}"
            }
        else :
            params = {
                "term": f"{year}-{month}"
            }
        self.url=f"{self.base_url}?{urlencode(params)}"


    def _process_html(self):
        date = ""
        for row in self.html.xpath(".//div[@class='accordion-block my-3']//div"):

            classname = row.get("class")
            if classname == "result-heading teal-bg p-2 mb-3 text-center":
                date = row.xpath(".//h3/text()")[0]
            elif classname=="accordion-item case-result":
                dock = row.xpath(".//p[@class='case-number teal-text mb-0']/text()")[0]
                name = row.xpath(".//p[@class='case-name teal-text']/text()")[0]
                summ = row.xpath(".//div[@class='result-info']/p/text()")
                if summ:
                    summary = summ[0]
                else:
                    summary=""
                url = row.xpath(".//a[@class='download-link']/@href")[0]
                self.cases.append(
                    {
                        "date": date,
                        "docket": [dock],
                        "name": name,
                        "url": url,
                        "summary": summary,
                    }
                )

    def _download_backwards(self, dates: Tuple[date]) -> None:
        start = dates[0]
        end = dates[1]

        start_month = start.month
        start_year = start.year
        end_month = end.month
        end_year = end.year
        if start_year == end_year:
            while start_month <= end_month:
                self.set_url(start_month , start_year)
                self.html = self._download()
                self._process_html()
                start_month +=1
        else:
            while start_month <= 12:
                self.set_url(start_month , start_year)
                self.html = self._download()
                self._process_html()
                start_month +=1
            start_month=1
            while start_month <= end_month:
                self.set_url(start_month , end_year)
                self.html = self._download()
                self._process_html()
                start_month +=1



    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
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

    def get_court_name(self):
        return "Supreme Court of South Carolina"

    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "scscop_p"

    def get_state_name(self):
        return "South Carolina"
