from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        rows = self.html.xpath('//table[@class="table table-striped table-bordered cols-4"]/tbody/tr')
        # Extracted data
        for row in rows:
            date = row.xpath('./td[2]/text()')[0].strip()
            curr_date = datetime.strptime(date, "%m/%d/%y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            title = row.xpath('./td[3]/a/text()')[0].strip()
            pdf_url = row.xpath('./td[4]//a/@href')[0].strip()
            docket = row.xpath('./td[1]/text()')[0].strip()
            self.cases.append({
                "docket":[docket],
                "name":title,
                "date":date,
                "url":pdf_url
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year, end_date.year + 1):
            self.url = f"https://ago.nebraska.gov/opinions/archive?field_opinion_date_value={year}"
            self.parse()
            self.downloader_executed = False
        return 0

    def get_class_name(self):
        return "neb_ag"

    def get_court_type(self):
        return 'state'

    def get_state_name(self):
        return "Nebraska"

    def get_court_name(self):
        return "Opinions of the Nebraska Attorney General"