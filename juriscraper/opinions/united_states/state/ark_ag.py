from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        cards = self.html.xpath('//div[@class="card"]')

        ###################################################
        #################### DATE #########################
        #################### NOT #########################
        #################### FOUND #########################

        for card in cards:
            title_elem = card.xpath('.//h5[@class="card-title"]/text()')
            requester_elem = card.xpath('.//h6[@class="card-subtitle mb-2 text-muted"]/text()')
            summary_elem = card.xpath('.//p[@class="card-text"]/text()')
            pdf_url_elem = card.xpath('.//a[contains(@href, ".pdf")]/@href')

            docket = title_elem[0].replace("Opinion ", "").strip() if title_elem else ""
            date = docket.split("-")[0] if "-" in docket else ""
            title = requester_elem[0].replace("Requested by", "").strip() if requester_elem else ""
            summary = ' '.join([s.strip() for s in summary_elem if s.strip()]) if summary_elem else ""
            pdf_url = pdf_url_elem[0] if pdf_url_elem else ""

            self.cases.append({
                "date": date,
                "title": title,
                "summary": summary,
                "pdf_url": pdf_url,
                "docket": docket})

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year, end_date.year):
            page = 1
            flag = True
            while flag:
                self.url=f'https://ag-opinions.ark.org/?type=year&q={year}&page={page}'
                self.parse()
                next_page = self.html.xpath('//li[a[contains(normalize-space(.), "Next Page →")]]')
                if next_page is None:
                    flag=False
                self.downloader_executed=False
        return 0

    def get_class_name(self):
        return "ark_ag"

    def get_court_type(self):
        return 'state'

    def get_state_name(self):
        return "Arkansas"

    def get_court_name(self):
        return "Opinions of the Arkansas Attorney General"