from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"
        self.base="https://www.innb.uscourts.gov/judges-info/opinions?field_opinion_date_value[value][year]={}&field_judge_nid=All&title=&page={}"

    def make_url(self, year: int , page : int) -> str:
        return self.base.format(year, page)

    def _process_html(self) -> None:
        for row in self.html.xpath(".//div[contains(@class, 'view-opinions') and contains(@class, 'file-listing')]/div[@class='view-content']"):
            judge = ""
            for child in row.xpath('./*'):
                tag = child.tag.lower()
                dockets = []


                if tag == 'h3':
                    judge = child.xpath("./text()")[0]
                    continue

                url = child.xpath(".//div[@class='views-field views-field-title']//a/@href")[0]
                dockets.append(child.xpath(".//div[@class='views-field views-field-title']//a/text()")[0].strip())
                date = child.xpath(".//div[@class='views-field views-field-title']//a/span/text()")[0].strip()
                month , day , year = date.split('/')
                title = child.xpath(".//div[@class='views-field views-field-body']//p//text()")[0].strip()
                case_date = f"{day}/{month}/{year}"

                self.cases.append({
                    "name": title,
                    "url": url,
                    "docket": dockets,
                    "date": date,
                    "judge" : [judge]
                })


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:

        for year in range(start_date.year, end_date.year + 1):
            page = 0
            while True:
                self.url = self.make_url(year, page)
                self.html = self._download()
                div = self.html.xpath(".//div[contains(@class, 'view-opinions') and contains(@class, 'file-listing')]/div[@class='view-content']")
                if div :
                    self._process_html()
                else:
                    break
                page +=1
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
        return "bank_nd_ind"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "7th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court Northern District of Indiana"
