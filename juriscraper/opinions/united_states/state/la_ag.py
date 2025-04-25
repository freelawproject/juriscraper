from datetime import datetime

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

class Site(OpinionSiteLinear):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = "Published"

    def _process_html(self):
        opinion_cards = self.html.xpath('//div[contains(@class, "opinion-summary")]')
        for card in opinion_cards:
            date = card.xpath('.//div[@class="card-footer"]/b/text()')[0].replace('Released: ', '').strip()
            curr_date = datetime.strptime(date, "%m/%d/%Y").strftime("%d/%m/%Y")
            res = CasemineUtil.compare_date(self.crawled_till, curr_date)
            if res == 1:
                return
            docket = card.xpath('.//h5[@class="card-title"]/text()')[0].replace('Opinion: ', '').strip()
            description = card.xpath('.//p[@class="card-text"]/text()')[0].strip()
            pdf_url = card.xpath('.//div[@class="card-footer"]/a/@href')[0].strip()
            self.cases.append({
                'docket': [docket],
                'name': description,
                'date': date,
                'url': pdf_url
            })

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start_date.strftime("%m/%d/%Y")
        self.url="https://www.ag.state.la.us/Opinion/Search"
        self.method="POST"
        self.parameters={
            "SearchTerm": "",
            "StartDate": start_date.strftime("%m/%d/%Y"),
            "EndDate": end_date.strftime("%m/%d/%Y")
        }
        self.parse()
        return 0

    def get_class_name(self):
        return "la_ag"

    def get_court_type(self):
        return 'state'

    def get_state_name(self):
        return "Louisiana"

    def get_court_name(self):
        return "Opinions of the Louisiana Attorney General"