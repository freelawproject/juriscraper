# Scraper for Texas Criminal Court of Appeals
# CourtID: texcrimapp
# Court Short Name: TX
# Author: Michael Lissner
# Reviewer: None
# Date: 2015-09-02


from typing import Dict, List

from juriscraper.opinions.united_states.state import tex


class Site(tex.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "ccrimapp"
        self.checkbox = 1

    def get_opinions(self, html) -> List[Dict]:
        """Override from tex.py. See docstring there for more info

        :param html: page's HTML object
        :return List of opinions
        """
        opinions = []
        opinion_xpath = "//div[div[contains(text(), 'Case Events')]]//tr[td[text()='OPINION ISSD']]"
        link_xpath = (
            ".//tr[td[1]/a and td[2][not(contains(text(), 'Notice'))]]"
        )
        for opinion in html.xpath(opinion_xpath):
            op = {}
            link = opinion.xpath(link_xpath)
            if not link:
                continue

            op["disposition"] = opinion.xpath(".//td[3]/text()")[0]
            op["download_url"] = link[0].xpath("td/a/@href")[0]

            op_type = link[0].xpath("td[2]/text()")[0].strip()
            if op_type == "Original":
                op["type"] = "010combined"
            elif op_type == "Dissenting":
                op["type"] = "040dissent"
            elif op_type == "Concurring":
                op["type"] = "030concurrence"

            opinions.append(op)

        return opinions
