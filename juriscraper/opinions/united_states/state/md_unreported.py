import html
from datetime import date, datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"

    def _process_html(self) -> None:
        for row in self.html.xpath("//table//tbody//tr"):
            # court_nm = row.xpath("td[1]//text()")[0].strip()
            date = row.xpath("td[2]//text()")[0].strip()
            docket = row.xpath("td[3]//text()")[0].strip()
            pdf_url = row.xpath("td[3]//a[contains(@href,'pdf')]/@href")[0]
            # term = row.xpath("td[4]//text()")[0].strip()
            judge = row.xpath("td[5]//text()")[0].strip()
            appellant = row.xpath("td[6]//text()")[0].strip()
            respondent = row.xpath("td[7]//text()")[0].strip()
            self.cases.append({
                "name": f"{appellant} v. {respondent}",
                "url": pdf_url,
                "judge": [judge],
                "date": date,
                "docket": [docket]
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start_month = 1
        end_month = 12
        for year in range(start_date.year, end_date.year + 1):
            for month in range(start_month, end_month + 1):
                if str(month).__len__() == 1:
                    self.url = f'https://www.mdcourts.gov/appellate/unreportedopinions/list/{year}0{month}'
                else:
                    self.url = f'https://www.mdcourts.gov/appellate/unreportedopinions/list/{year}{month}'
                self.parse()
                self.downloader_executed = False
                if list(self.html.xpath("//table")).__len__() == 0:
                    break
        return 0

    def get_class_name(self):
        return "md_unreported"

    def get_court_name(self):
        return "Maryland Court of Special Appeals"

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "Maryland"
