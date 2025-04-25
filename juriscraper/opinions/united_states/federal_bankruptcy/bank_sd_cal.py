from datetime import datetime

from lxml import html
from pkg_resources.extern import names

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base="https://www.casb.uscourts.gov/opinions?field_opinion_date_value%5Bvalue%5D%5Byear%5D={}&field_opinion_judge_tid=All&field_publish_status_value_1=All"

    def make_url(self, year: int) -> str:
        return self.base.format(year)

    def _process_html(self) -> None:
        for row in self.html.xpath(".//div[contains(@class, 'view-opinions') and contains(@class, 'file-listing')]/div[@class='view-content']/table"):
            # print(html.tostring(row,pretty_print=True).decode('UTF-8'))
            status = row.xpath(".//caption/text()")[0].strip()
            date = row.xpath(".//tbody/tr/td[1]/span/text()")[0].strip()
            names = row.xpath(".//tbody/tr/td[2]/a/text()")[0].strip()
            url = row.xpath(".//tbody/tr/td[2]/a/@href")[0].strip()
            judge = row.xpath(".//tbody/tr/td[3]/text()")[0].strip()
            main_case=""
            month, day, year = date.split('/')
            case_date = f"{day}/{month}/{year}"

            parts = names.split()
            docket = parts[0]
            if parts[1] == "(main":
                main_case = " ".join(parts[1:5])
                name = " ".join(parts[5:])
            else:
                name = " ".join(parts[1:])

            self.cases.append({
                "name": name,
                "url": url,
                "docket": [docket],
                "date": date,
                "judge": [judge],
                "status":status
            })


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:

        for year in range (start_date.year , end_date.year+1):
            self.url = self.make_url(year)
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
        return "bank_sd_cal"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "9th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court Southern District of California"
