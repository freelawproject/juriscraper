"""
Author: William Palin
Date created: 2023-01-16
Scraper for the Decisiones del Tribunal Supremo
CourtID: pr
Court Short Name: Puerto Rico
"""

from datetime import date

from dateparser import parse

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = date.today().year
        self.url = f"https://poderjudicial.pr/index.php/tribunal-supremo/decisiones-del-tribunal-supremo/decisiones-del-tribunal-supremo-{year}/"
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath(".//table/tbody/tr/td/a/@href/../../.."):
            cells = row.xpath(".//td")
            citation = cells[0].text_content()
            url = cells[0].xpath(".//a/@href")[0]
            date_obj = parse(cells[4].text_content(), languages=["es"])
            if not date_obj:
                # This is to handle the junk on the website in one row
                continue
            self.cases.append(
                {
                    "name": cells[3].text_content(),
                    "url": url,
                    "citation": citation,
                    "docket": cells[2].text_content(),
                    "date": str(date_obj.date()),
                }
            )
