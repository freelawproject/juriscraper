from datetime import datetime

from PIL.ImageChops import offset
from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def check_len(self, field):
        if list(field).__len__()==0:
            return ""
        else:
            return field[0].strip()


    def _process_html(self):
        divs = self.html.xpath('//div[contains(@class, "opinionSearchResult")]')
        for div in divs:
            date = self.check_len(div.xpath("./table/tr[3]/td[4]/text()"))
            curr_date = datetime.strptime(date, "%m/%d/%Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            title =  self.check_len(div.xpath("./table/tr[1]/td[2]/text()"))
            type = self.check_len(div.xpath("./table/tr[1]/td[4]/text()"))
            docket = self.check_len(div.xpath("./table/tr[2]/td[2]/text()"))
            advisory = self.check_len(div.xpath("./table/tr[2]/td[4]/text()"))
            judge = self.check_len(div.xpath("./table/tr[3]/td[2]/text()"))
            pdfurl = self.check_len(div.xpath("./table/tr[4]//a/@href"))
            # print(f"{date} || {docket} || {title} || {advisory} || {judge} || {pdfurl}")
            self.cases.append({
                "name":title,
                "type": type,
                "docket": [docket],
                "adversary_number": advisory,
                "url":pdfurl, "judge": [judge],
                "date":date
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        page = 0
        flag=True
        sdate=start_date.strftime("%m/%d/%Y").replace("/","%2F")
        edate = end_date.strftime("%m/%d/%Y").replace("/", "%2F")
        while flag:
            self.url=f'https://apps.mieb.uscourts.gov/opinions/search/result?advanceSearch=Search&bkType=&criteria=%2A&from={sdate}&judge=&limit=20&sortBy=relevance&to={edate}&offset={page}'
            self.parse()
            last_page_div = self.html.xpath("//div[@class='pagination']/a[contains(text(), 'Next >')]")
            if list(last_page_div).__len__()==0:
                flag=False
            self.downloader_executed=False
            page+=20
        return 0

    def get_class_name(self):
        return "bank_ed_mich"

    def get_court_type(self):
        return "Bankruptcy"

    def get_state_name(self):
        return "6th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court Eastern District of Michigan"