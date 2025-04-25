from datetime import datetime
import html

from lxml import html
import requests

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"
        self.current_year = None
        self.court_code = "full-commission-opinions"

    def _process_html(self):
        uls = self.html.xpath('//ul[@class="month-list"]')
        for ul in uls:
            lis = ul.xpath("./li")
            for li in lis:
                url = str(li.xpath("./a/@href")[0]).strip()
                title = str(li.xpath("./a/text()")[0]).strip()
                if str(li.xpath("./a/text()")[1]).startswith("AWCC"):
                    docket = str(li.xpath("./a/text()")[1]).replace("AWCC#","").replace("\t","").strip().replace("&",",").split(",")
                    cleaned_list = [item.strip() for item in docket if item.strip()]
                    date = str(li.xpath("./a/text()")[2]).strip()
                else:
                    docket = str(li.xpath("./a/text()")[2]).replace("AWCC#", "").replace("\t", "").strip().replace("&", ",").split(",")
                    cleaned_list = [item.strip() for item in docket if item.strip()]
                    date = str(li.xpath("./a/text()")[3]).strip()
                curr_date = datetime.strptime(date, "%B %d, %Y").strftime("%d/%m/%Y")
                res = CasemineUtil.compare_date(self.crawled_till, curr_date)
                if res == 1:
                    return
                # print(f"{date} || {cleaned_list} || {title} || {url}")
                self.cases.append({
                    "date":date,
                    "docket":cleaned_list,
                    "url":url,
                    "name":title
                })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.url = f"https://labor.arkansas.gov/workers-comp/awcc-opinions/{self.court_code}/"
        self.parse()
        return 0

    def get_class_name(self):
        return "ark_work_comp"

    def get_court_type(self):
        return 'state'

    def get_state_name(self):
        return "Arkansas"

    def get_court_name(self):
        return "Arkansas Workers' Compensation Commission"