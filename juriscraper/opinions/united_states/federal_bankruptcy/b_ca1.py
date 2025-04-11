from datetime import date, datetime, timedelta
import json
import requests

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        rows = self.html.xpath('//table[@class="views-table cols-4"]/tbody/tr')
        for row in rows:
            date = row.xpath('.//td[3]/span/text()')[0].strip()
            curr_date = datetime.strptime(date, "%Y/%m/%d").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            docket = \
            row.xpath('.//td[2]/a/text()')[
                0].strip()
            pdf_url = \
            row.xpath('.//td[1]/a/@href')[
                0].strip()
            title = \
            row.xpath('.//td[4]/text()[1]')[
                0].strip()
            lower_court = \
            row.xpath('.//td[4]/span/text()')[
                0].strip()
            self.cases.append({
                "date":date,
                "docket":[docket],
                "url":pdf_url,
                "name":title,
                "lower_court":lower_court
            })


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        sdate = start_date.strftime("%m/%d/%Y").replace("/", "%2F")
        edate = end_date.strftime("%m/%d/%Y").replace("/", "%2F")
        self.url=f'https://www.bap1.uscourts.gov/bapopn?opn=&field_opn_short_title_value=&field_opn_issdate_value%5Bmin%5D%5Bdate%5D={sdate}&field_opn_issdate_value%5Bmax%5D%5Bdate%5D={edate}'
        self.parse()
        return 0

    def get_class_name(self):
        return "b_ca1"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "1st Circuit"

    def get_court_name(self):
        return "Bankruptcy Court for the First Circuit"
