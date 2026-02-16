# Scraper for Texas Criminal Court of Appeals
# CourtID: texcrimapp
# Court Short Name: TX
# Author: Michael Lissner
# Reviewer: None
# Date: 2015-09-02


from juriscraper.AbstractSite import logger
from juriscraper.lib.type_utils import OpinionType
from juriscraper.opinions.united_states.state import texapp


class Site(texapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.checkbox = 1

    def get_opinions(self, html, _) -> tuple[list[dict], str]:
        """Override from texapp.py. See docstring there for more info

        :param html: page's HTML object
        :return List of opinions
        """
        opinions = []
        opinion_xpath = "//div[div[contains(text(), 'Case Events')]]//tr[td[text()='OPINION ISSD']]"
        link_xpath = (
            ".//tr[td[1]/a and td[2][not(contains(text(), 'Notice'))]]"
        )
        disposition = ""

        for opinion in html.xpath(opinion_xpath):
            op = {}
            link = opinion.xpath(link_xpath)
            if not link:
                logger.info(
                    "Skipping row with no link %s", opinion.xpath("string")
                )
                continue

            op["url"] = link[0].xpath("td/a/@href")[0]

            op_type = link[0].xpath("td[2]/text()")[0].strip()
            if op_type == "Original":
                # use the 'main' opinion disposition as cluster disposition
                disposition = opinion.xpath(".//td[3]/text()")[0]
                op["type"] = OpinionType.MAJORITY.value
            elif op_type == "Concurring & Dissenting":
                op["type"] = (
                    OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART.value
                )
            elif op_type == "Dissenting":
                op["type"] = OpinionType.DISSENT.value
            elif op_type == "Concurring":
                op["type"] = OpinionType.CONCURRENCE.value

            opinions.append(op)

        return opinions, disposition
