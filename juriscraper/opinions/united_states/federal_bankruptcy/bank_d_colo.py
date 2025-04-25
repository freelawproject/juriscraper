import re
from datetime import datetime

from lxml import html
from numpy.core.defchararray import title

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"
        self.base="https://www.cob.uscourts.gov/judges-info/opinions?field_opinion_date_value%5Bvalue%5D%5Byear%5D={}&field_judge_nid=All&page={}"

    def make_url(self, year: int , page : int) -> str:
        return self.base.format(year, page)

    def _process_html(self) -> None:
        for row in self.html.xpath(".//div['view-content']//div[contains(concat(' ', normalize-space(@class), ' '), ' views-row ')]"):
            text=row.xpath(".//div[1]/span/a/text()")[0]
            url = row.xpath(".//div[1]/span/a/@href")[0]
            # text="In re Peak Serum, Inc., Case No. 19-19802 JGR Order entered December 8, 2020 (retroactive application of SBRA and CARES Act, and dismissal v. appointment of Chapter 11 trustee in jointly administered cases) 12/08/2020"
            summ = ""
            date = row.xpath(".//div[1]/span/a/span/text()")[0]
            month, day, year = date.split('/')
            case_date = f"{day}/{month}/{year}"
            for p in row.xpath(".//div[2]//p"):
                summ += p.xpath(".//text()")[0]

            match = re.search(r'No\.?\s+([^\s,]+(?:\s+[A-Z]+)?)', text)
            docket= match.group(1) if match else None

            name = text.split(',')[0].strip()

            self.cases.append({
                "name": name,
                "url": url,
                "summary":summ,
                "docket": [docket],
                "date": date,
            })


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year, end_date.year + 1):
            page = 0
            while True:
                self.url = self.make_url(year, page)
                self.html = self._download()
                div = self.html.xpath(".//div[@class='view-content']")
                if div:
                    self._process_html()
                else:
                    break
                page += 1

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
        return "bank_d_colo"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "10th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court District of Colorado"
