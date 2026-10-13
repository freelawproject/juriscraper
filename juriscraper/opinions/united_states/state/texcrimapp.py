# Scraper for Texas Criminal Court of Appeals
# CourtID: texcrimapp
# Court Short Name: TX
# Author: Michael Lissner
# Reviewer: None
# Date: 2015-09-02

from datetime import date

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import OpinionType, RawOpinion
from juriscraper.opinions.united_states.state import texapp


class Site(texapp.Site):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.checkbox = 1

    @override
    def get_opinions(
        self, html: HtmlElement, op_date: str
    ) -> tuple[list[RawOpinion], str]:
        """Override from texapp.py. See docstring there for more info

        :param html: page's HTML object
        :param op_date: date to identify related opinions of a case
        :return: List of opinions
        """
        opinions: list[RawOpinion] = []
        opinion_xpath = "//div[div[contains(text(), 'Case Events')]]//tr[td[text()='OPINION ISSD']]"
        link_xpath = (
            ".//tr[td[1]/a and td[2][not(contains(text(), 'Notice'))]]"
        )
        disposition = ""

        opinion_matches: list[HtmlElement] = html.xpath(opinion_xpath)
        for opinion in opinion_matches:
            op: RawOpinion = {}
            link: list[HtmlElement] = opinion.xpath(link_xpath)
            if not bool(link):
                logger.info(
                    "Skipping row with no link %s",
                    opinion.findall("string"),
                )
                continue

            op["url"] = link[0].xpath("td/a/@href")[0]

            op_type: str = link[0].xpath("td[2]/text()")[0].strip()
            if op_type == "Original":
                # use the 'main' opinion disposition as cluster disposition
                disposition: str = opinion.xpath(".//td[3]/text()")[0]
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
