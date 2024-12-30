"""Scraper for the California Attorney General
CourtID: calag
Court Short Name: California Attorney General
"""

import datetime

from lxml.html import HtmlElement

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.url = f"https://oag.ca.gov/opinions/yearly-index?conclusion-year[value][year]={self.year}"
        self.back_scrape_iterable = list(range(1985, self.year + 1))
        self.cipher = "ECDHE-RSA-AES128-GCM-SHA256"
        self.set_custom_adapter(self.cipher)
        self.status = "Published"

    def build_summaries(self, row: HtmlElement) -> str:
        """Build Summaries of opinions

        :param row: Row to collect from
        :return: Summary of the opinion
        """
        questions = row.xpath("./td[2]")[0].text_content()
        conclusions = row.xpath("./td[3]")[0].text_content()
        return f"QUESTIONS: {questions} CONCLUSIONS: {conclusions}"

    def _process_html(self) -> None:
        """Process California AG HTML

        :return: none
        """
        for row in self.html.xpath("//table/tbody/tr[.//a]"):
            docket = row.xpath(".//a//strong/text()")[0].strip()
            # Citation may not exist (yet?)
            citation = row.xpath(".//strong/em/text()")
            self.cases.append(
                {
                    "url": row.xpath(".//a/@href")[0],
                    "citation": citation[0] if citation else "",
                    "docket": docket,
                    "date": row.xpath(".//td/span/text()")[0].strip(),
                    "name": f"California Attorney General Opinion {docket}",
                    "summary": self.build_summaries(row),
                }
            )

    def _download_backwards(self, year: str) -> None:
        """Download backwards

        :param year: The year to scrape
        :return: None
        """
        self.url = f"https://oag.ca.gov/opinions/yearly-index?conclusion-year[value][year]={year}"
