from datetime import datetime

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        rows = self.html.xpath('//table[@id="ts"]/tbody/tr')
        for row in rows:
            date = row.xpath('./td[1]/text()')[0].strip()
            curr_date = datetime.strptime(date, "%m/%d/%Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            # Docket and title
            docket = row.xpath('./td[2]/text()[1]')[0].replace('Case No.',"").strip()  # Case No.
            title = row.xpath('./td[2]/text()[2]')[0].strip()  # Party name or case title

            # PDF links
            pdf_links = row.xpath('./td[3]//a/@href')
            pdf_urls = [ link for link in pdf_links]  # adjust base URL if needed

            # Judge
            judge_line = row.xpath('./td[3]//text()[contains(., "Judge")]')
            judge = judge_line[0].replace('by', '').strip() if judge_line else ''
            self.cases.append({
                'date': date, 'docket': [docket], 'name': title, 'url': pdf_urls[0], 'judge': [judge]})

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.url=f'https://ecf.dcb.uscourts.gov/cgi-bin/Opinions.pl'
        self.parse()
        return 0

    def get_class_name(self):
        return "bank_dc"

    def get_court_type(self):
        return 'Bankruptcy'

    def get_state_name(self):
        return "District of Columbia Circuit"

    def get_court_name(self):
        return "Bankruptcy Court for the District of Columbia"