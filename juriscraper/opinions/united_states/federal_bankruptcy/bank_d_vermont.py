from datetime import date, datetime, timedelta
import json
import re

import requests

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        opinions = self.html.xpath('//div[contains(@class, "views-row")]')
        results = []
        for opinion in opinions:
            opinion_type = opinion.xpath('.//div[contains(@class, "views-field-body")]/div/p/text()')[0].strip()
            if not str(opinion_type).__contains__('Memorandum'):
                continue
            title = opinion.xpath('.//div[contains(@class, "views-field-title")]//a/text()[1]')[0].strip()
            date = opinion.xpath('.//span[@class="date-display-single"]/text()')[0]
            curr_date = datetime.strptime(date, "%m/%d/%Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            pdfurl = opinion.xpath('.//div[contains(@class, "views-field-title")]//a/@href')[0]
            docket_match = re.search(r"\((.*?)\)", title)
            docket = docket_match.group(1) if docket_match else ""
            doc_list=re.findall(r'\d{2}-\d{5}', docket)
            new_title=str(title).replace(docket,"").replace(")","").replace("(","").strip()
            self.cases.append({
                "name": new_title, "date": date, "docket": doc_list, "url": pdfurl,})

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year,end_date.year+1):
            self.url=f'https://www.vtb.uscourts.gov/judges-info/opinions?field_opinion_date_value%5Bvalue%5D%5Byear%5D={year}&field_judge_nid=All'
            self.parse()
            self.downloader_executed=False
        return 0

    def get_class_name(self):
        return "bank_d_vermont"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "2d Circuit"

    def get_court_name(self):
        return "Bankruptcy Court District of Vermont"