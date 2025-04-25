import re

from lxml import html

from juriscraper.opinions.united_states.federal_bankruptcy import bank_nd_ind


class Site(bank_nd_ind.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base="https://www.mnb.uscourts.gov/judges-info/opinions?field_opinion_date_value%5Bvalue%5D%5Byear%5D={}&field_judge_nid=All&page={}"

    def _process_html(self) -> None:
        for row in self.html.xpath(".//div[contains(@class, 'view-opinions') and contains(@class, 'file-listing')]//div[@class='item-list']/ul/li"):
            url = row.xpath(".//div[@class='views-field views-field-title']//a/@href")[0]
            title = row.xpath(".//div[@class='views-field views-field-title']//a/text()")[0].strip()
            dockets = re.findall(r'(Adv\.?\s*\d{2}-\d+|Bky\s*\d{2}-\d+)', title)

            name = re.sub(r'(,?\s*(Adv\.?\s*\d{2}-\d+|Bky\s*\d{2}-\d+))', '',
                           title).strip()
            date = row.xpath(".//div[@class='views-field views-field-title']//a/span/text()")[0].strip()

            self.cases.append({
                "name": name,
                "url": url,
                "docket": dockets,
                "date":date
            })

    def get_class_name(self):
        return "bank_d_minn"

    def get_state_name(self):
        return "8th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court District of Minnesota"
