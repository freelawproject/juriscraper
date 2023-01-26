"""
Author: William Palin
Date created: 2023-01-16
Scraper for the Decisiones del Tribunal Supremo
CourtID: pr
Court Short Name: Puerto Rico
"""

import locale
from datetime import date, datetime
from typing import Optional

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
        self.court_id = self.__module__
        year = date.today().year
        self.url = f"https://poderjudicial.pr/index.php/tribunal-supremo/decisiones-del-tribunal-supremo/decisiones-del-tribunal-supremo-{year}/"
        self.status = "Published"

    def handle_spanish_dates(self, cells) -> Optional[str]:
        """Convert dates from spanish to english to process

        Using multiple formats and ignore the bad data on the website
        Parse either of the two spanish formats

        :param cells: Table Cells in the row
        :return:
        """
        try:
            date_str = cells[4].text_content().replace("\xa0", "")
            try:
                date_str = datetime.strptime(date_str, "%d de %B de %Y")
            except:
                date_str = datetime.strptime(date_str, "%d %B %Y")
            return str(date_str.date())
        except ValueError:
            return None

    def _process_html(self):
        for row in self.html.xpath(".//table/tbody/tr/td/a/@href/../../.."):
            cells = row.xpath(".//td")
            citation = cells[0].text_content()
            url = cells[0].xpath(".//a/@href")[0]
            date_str = self.handle_spanish_dates(cells)
            if not date_str:
                # This is to handle the junk on the website in one row
                continue
            self.cases.append(
                {
                    "name": cells[3].text_content(),
                    "url": url,
                    "citation": citation,
                    "docket": cells[2].text_content(),
                    "date": date_str,
                }
            )
