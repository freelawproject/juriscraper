from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        rows = self.html.xpath('//div[contains(@class, "views-row")]')
        for row in rows:
            title = row.xpath('.//div[contains(@class, "views-field-title")]//a/text()[1]')[0]
            url = row.xpath('.//div[contains(@class, "views-field-title")]//a/@href')[0]
            date = row.xpath('.//span[@class="date-display-single"]/text()')[0]
            curr_date = datetime.strptime(date, "%m/%d/%Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            case_number = row.xpath('.//div[contains(@class, "views-field-field-case-number-opinion")]//div/text()')
            judge = row.xpath('.//div[contains(@class, "views-field-field-judge")]//div/text()')
            body = row.xpath('.//div[contains(@class, "views-field-body")]//div//p/text()')[1]
            # print(f"{date} || {case_number} || {judge} || {title} || {url} || {body}")
            self.cases.append({
                "name":title,
                "url":url,
                "docket":case_number,
                "date":date,
                "summary":body,
                "judge":judge
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year,end_date.year+1):
            page = 0
            flag=True
            while flag:
                self.url=f'https://www.wvsd.uscourts.gov/judges-info/opinions?field_opinion_date_value%5Bvalue%5D%5Byear%5D={year}&field_judge_nid=All&page={page}'
                self.parse()
                last_page_div=self.html.xpath('//div[@class="view-empty"]')
                if list(last_page_div).__len__() !=0:
                    flag=False
                self.downloader_executed=False
                page+=1
        return 0

    def get_class_name(self):
        return "bank_sd_wv"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "4th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court Southern District of West Virginia"