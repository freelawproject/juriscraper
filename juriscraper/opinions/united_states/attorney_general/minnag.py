"""Scraper for Minnesota Attorney General Opinions
CourtID: minnag
Court Short Name: MN
Author: David Cook
Reviewer:
"""

import re

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.domain = "http://www.ag.state.mn.us"
        self.url = "http://www.ag.state.mn.us/office/opinions/DATE.asp"
        self.opinions = []

    def _download(self, request_dict={}):
        html = super()._download(request_dict)
        self._extract_case_data_from_html(html)
        return html

    def _extract_case_data_from_html(self, html):
        for p in html.xpath("//div[@id='content']/div[@id='op']/p"):
            text = p.xpath("a/strong/following-sibling::text()[1]")[0]
            name = " ".join(
                text.split()[1:]
            )  # strip leading dash charater, which can be one of various unicode dash characters
            name = re.sub("\\s+", " ", name).strip()
            summary = " ".join(
                p.xpath(
                    "br/following-sibling::text() | br/following-sibling::*//text()"
                )
            )
            summary = re.sub("\\s+", " ", summary).strip()

            self.opinions.append(
                {
                    "name": name,
                    "url": p.xpath("a/@href")[0],
                    "date": convert_date_string(p.xpath("a/strong/text()")[0]),
                    "summary": summary,
                }
            )

    def _get_case_names(self):
        return [opinion["name"] for opinion in self.opinions]

    def _get_download_urls(self):
        return [opinion["url"] for opinion in self.opinions]

    def _get_case_dates(self):
        return [opinion["date"] for opinion in self.opinions]

    def _get_summaries(self):
        return [opinion["summary"] for opinion in self.opinions]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.opinions)
