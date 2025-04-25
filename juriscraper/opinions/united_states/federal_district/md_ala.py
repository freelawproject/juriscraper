from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        rows = self.html.xpath('//tbody/tr')
        for row in rows:
            date = row.xpath('./td[1]/text()[1]')[0].strip()
            curr_date = datetime.strptime(date,"%m/%d/%Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            # Extract docket type and number
            docket_text = row.xpath('./td[2]//text()[1]')[0].strip()  # E.g., "Civil Action No. 2021-0832"
            docket = docket_text.split(' No. ')[1]  # E.g., "2021-0832"
            # Extract case title (next text node after <br>)
            title = row.xpath('./td[2]//text()[2]')[0].strip()
            pdf_url = row.xpath('./td[3]/a[1]/@href')[0]
            texts = row.xpath('./td[3]//text()')
            presiding_judge = ''
            signed_by = ''
            for t in texts:
                if "Presiding Judge:" in t:
                    presiding_judge = t.split("Presiding Judge:")[1].strip()
                elif "Signed by:" in t:
                    signed_by = t.split("Signed by:")[1].strip()
            # print(f"{date} || {title} || {docket} || {presiding_judge} || {signed_by} || {pdf_url}")
            judges = []
            if not presiding_judge.__eq__(signed_by):
                judges.append(presiding_judge)
                judges.append(signed_by)
            else:
                judges.append(presiding_judge)
            self.cases.append({
                "name":title,
                "url":pdf_url,
                "docket":[docket],
                "date":date,
                "judge":judges
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year,end_date.year+1):
            self.url=f'https://ecf.almd.uscourts.gov/cgi-bin/Opinions.pl?{year}'
            self.parse()
            self.downloader_executed=False
        return 0

    def get_class_name(self):
        return "md_ala"

    def get_court_type(self):
        return 'Federal'

    def get_state_name(self):
        return "11th Circuit"

    def get_court_name(self):
        return "Middle District of Alabama"