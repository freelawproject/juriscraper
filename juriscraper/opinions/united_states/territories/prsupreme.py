"""
Author: William Palin
Date created: 2023-01-16
Scraper for the Decisiones del Tribunal Supremo
CourtID: pr
Court Short Name: Puerto Rico
"""

from datetime import date, datetime

from dateparser import parse

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = "1998/01/01"
    base_url = "https://poderjudicial.pr/index.php/tribunal-supremo/decisiones-del-tribunal-supremo/decisiones-del-tribunal-supremo"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().year
        self.url = f"{self.base_url}-{self.year}/"
        self.status = "Published"
        self.request["verify"] = False
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        for link in self.html.xpath("//a[contains(string(.), 'TSPR')]"):
            url = link.xpath("@href")[0]
            citation = link.xpath("string(.)").strip()
            cells = link.xpath(
                "ancestor::tr[1]/following-sibling::tr[position() <= 5]"
            )
            date_str = cells[3].xpath(".//td")[1].text_content().strip()
            date_obj = parse(date_str, languages=["es"])

            if not date_obj:
                logger.info("Skipping row", citation)
                continue

            self.cases.append(
                {
                    "name": cells[1].text_content().strip().split("\n")[1],
                    "url": url,
                    "citation": citation.strip(),
                    "docket": cells[0].text_content().strip().split("\n")[1],
                    "date": str(date_obj.date()),
                }
            )

    def make_backscrape_iterable(self, kwargs):
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if not start:
            return

        start_date = datetime.strptime(start, "%Y/%m/%d")
        end_date = datetime.strptime(end, "%Y/%m/%d")

        self.back_scrape_iterable = range(start_date.year, end_date.year + 1)

    def _download_backwards(self, year):
        self.url = f"{self.base_url}-{year}/"
        self.html = self._download()
        self._process_html()
