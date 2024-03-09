# Scraper for Texas 1st Court of Appeals
# CourtID: texapp1
# Court Short Name: TX
# Author: Andrei Chelaru
# Reviewer:
# Date: 2014-07-10

from typing import Dict, List

from juriscraper.opinions.united_states.state import tex


class Site(tex.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "capp_1"
        self.checkbox = 2

    def get_opinions(self, html) -> List[Dict]:
        """Override from tex.py. See docstring there for more info

        :param html: page's HTML object
        :return List of opinions
        """
        opinions = []
        opinion_xpath = "//div[div[contains(text(), 'Case Events')]]//tr[td[contains(text(), 'pinion issued')]]"
        link_xpath = ".//tr[td[1]/a and td[2][contains(text(), 'pinion')]]"
        for opinion in html.xpath(opinion_xpath):
            op = {}
            link = opinion.xpath(link_xpath)
            if not link:
                continue

            op["disposition"] = opinion.xpath(".//td[3]/text()")[0]
            op["download_url"] = link[0].xpath("td/a/@href")[0]

            op_type = link[0].xpath("td[2]/text()")[0].strip().lower()
            if "concur" in op_type:
                op["type"] = "030concurrence"
            elif "diss" in op_type:
                op["type"] = "040dissent"
            else:
                op["type"] = "010combined"

            opinions.append(op)

        return opinions
