from datetime import date, datetime, timedelta
import json
import re

from lxml import html
import requests

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        # Extract all opinion entries
        entries = self.html.xpath('//div[contains(@class, "views-row")]')
        for entry in entries:
            # Extract each field with error handling
            title = entry.xpath('.//div[contains(@class, "views-field-title")]/span[@class="field-content"]/a/text()')[0].replace("Judge:","").strip()
            pdf_url = entry.xpath('.//div[contains(@class, "views-field-title")]/span[@class="field-content"]/a/@href')[0]
            summary = entry.xpath('.//div[contains(@class, "views-field-body")]/div/p/text()')[0]

            doc_list=re.findall(r'\d{2}-\d{5}|\d{2}-\d{4}', title)
            new_title=str(title).replace("No.","").replace("Adv.","").replace("A.P.","").replace("(","").replace(")","").replace(doc_list.__getitem__(0),"").strip()
            date = (entry.xpath('.//span[@class="date-display-single"]/text()') or [''])[0].strip()
            curr_date = datetime.strptime(date, "%m/%d/%Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            self.cases.append({
                "name":new_title,
                "url":pdf_url,
                "docket":doc_list,
                "date":date,
                "summary":summary
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year,end_date.year+1):
            self.url=f'https://www.ncmb.uscourts.gov/judges-info/opinions?field_opinion_date_value%5Bvalue%5D%5Byear%5D={year}&field_judge_nid=All&items_per_page=All'
            self.parse()
            self.downloader_executed=False
        return 0

    def get_class_name(self):
        return "bank_md_nc"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "4th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court Middle District of North Carolina"