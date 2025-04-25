import re

from lxml import html

from juriscraper.opinions.united_states.federal_bankruptcy import bank_nd_ind


class Site(bank_nd_ind.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base="https://www.orb.uscourts.gov/judges/opinions?field_opinion_date_value[value][year]={}&field_opinion_judge_tid=All&page={}"

    def _process_html(self) -> None:
        for row in self.html.xpath(".//table[@class= 'views-table cols-4']//tbody/tr"):
            url = row.xpath(".//td[2]//a/@href")[0]
            title = row.xpath(".//td[2]//a/text()")[0].strip()
            docket = row.xpath(".//td[3]/text()")[0].strip()
            date = row.xpath(".//td[1]/span/text()")[0].strip()
            self.cases.append({
                "name": title,
                "url": url,
                "docket": docket.split('; '),
                "date":date
            })

    def get_class_name(self):
        return "bank_d_or"

    def get_state_name(self):
        return "9th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court District of Oregon"
