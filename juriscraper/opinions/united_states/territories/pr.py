"""
Author: William Palin
Date created: 2023-01-16
Scraper for the Decisiones del Tribunal Supremo
CourtID: pr
Court Short Name: Puerto Rico
"""

from datetime import date, datetime
from typing import Optional

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = date.today().year
        self.url = f"https://poderjudicial.pr/index.php/tribunal-supremo/decisiones-del-tribunal-supremo/decisiones-del-tribunal-supremo-{year}/"
        self.status = "Published"

    def handle_spanish_dates(self, cells) -> Optional[str]:
        """Convert dates from spanish to english to process

        :param cells:
        :return:
        """
        spanish_months = {
            "enero": "January",
            "febrero": "February",
            "marzo": "March",
            "abril": "April",
            "mayo": "May",
            "junio": "June",
            "julio": "July",
            "agosto": "August",
            "septiembre": "September",
            "octubre": "October",
            "noviembre": "November",
            "diciembre": "December",
        }
        try:
            date_str = cells[4].text_content()
            date_str = date_str.replace("\xa0", "")
            date_str = date_str.replace(" de ", " ")
            for k, v in spanish_months.items():
                date_str = date_str.replace(k, v)
            datetime_str = datetime.strptime(date_str, "%d %B %Y")
            return str(datetime_str.date())
        except ValueError:
            return None

    def _process_html(self):
        for row in self.html.xpath(".//table/tbody/tr"):
            cells = row.xpath(".//td")
            citation = cells[0].text_content()
            maybe_link = cells[0].xpath(".//a/@href")
            if not maybe_link:
                continue
            else:
                url = maybe_link[0]
            date_str = self.handle_spanish_dates(cells)
            if not date_str:
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
