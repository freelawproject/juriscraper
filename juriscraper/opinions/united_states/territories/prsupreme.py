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
            cells = row.xpath("following-sibling::tr[position() <= 5]")
            citation = row.text_content()
            url = row.xpath(".//a/@href")[0]
            date_str = cells[3].text_content().strip().split("\n")[1]
            date_obj = parse(date_str, languages=["es"])
            if not date_obj:
                # This is to handle the junk on the website in one row
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
