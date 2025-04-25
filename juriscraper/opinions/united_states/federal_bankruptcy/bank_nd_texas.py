from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        rows = self.html.xpath('//table[contains(@class, "views-table")]/tbody/tr')
        for row in rows:
            docket = row.xpath("substring-before(normalize-space(td[1]/a/text()[1]), ' ')")
            date = row.xpath("td[1]/a/span[@class='date-display-single']/text()")[0]
            curr_date = datetime.strptime(date, "%m/%d/%Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            title = row.xpath("normalize-space(substring-after(td[1]/a/text()[1], ' '))")
            pdfurl = row.xpath("td[1]/a/@href")[0]
            self.cases.append({
                "name":title,
                "url":pdfurl,
                "docket":[docket],
                "date":date,
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year,end_date.year+1):
            page = 0
            flag=True
            while flag:
                self.url=f'https://www.txnb.uscourts.gov/opinions?field_opinion_date_value%5Bvalue%5D%5Byear%5D={year}&field_judge_nid=All&page={page}'
                self.parse()
                last_page_div = self.html.xpath("//ul[@class='pager']/li[contains(@class, 'pager__item--next')]")
                if list(last_page_div).__len__()==0:
                    flag=False
                self.downloader_executed=False
                page+=1
        return 0

    def get_class_name(self):
        return "bank_nd_texas"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "5th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court Northern District of Texas"