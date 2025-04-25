from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url="https://www.ca9.uscourts.gov/bap/#"


    def _process_html(self) -> None:
        count = 0
        for row in self.html.xpath(".//table[@id = 'search-results-table']//tr"):
            if count ==0:
                count += 1
                continue
            name = row.xpath(".//td[1]/a/text()")[0]
            url = row.xpath(".//td[1]/a/@href")[0]
            type = row.xpath(".//td[2]/text()")[0]
            docket = row.xpath(".//td[3]/text()")[0].split(';')
            date = row.xpath(".//td[4]/text()")[0]
            month , day , year = date.split('/')
            case_date = f"{day}/{month}/{year}"
            self.cases.append({
                "name": name,
                "url": url,
                "docket": docket,
                "date": date,
                "status" : type.split(' ')[0]
                })


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        if not self.downloader_executed:
            self.html = self._download()
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
        return 0

    def get_class_name(self):
        return "b_ca9"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "9th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court of Appeal for the Ninth Circuit"
