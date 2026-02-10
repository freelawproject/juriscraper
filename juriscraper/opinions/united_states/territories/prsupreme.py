"""
Author: William Palin
Date created: 2023-01-16
Scraper for the Decisiones del Tribunal Supremo
CourtID: pr
Court Short Name: Puerto Rico
"""

import re
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
        # In 2023, the website changed from a horizontal table layout
        # (one row per case, 6 TDs) to a vertical layout (6 rows per case,
        # each with a label/value TD pair). We detect the format by counting
        # sibling TDs: 5 siblings means old format, 0 means new format.
        cells_in_tr_xpath = (
            "ancestor::tr[1]/following-sibling::tr[position() <= 5]"
        )
        cells_in_td_xpath = "ancestor::td[1]/following-sibling::td"

        for link in self.html.xpath("//a[contains(string(.), 'TSPR')]"):
            url = link.xpath("@href")[0]
            citation = link.xpath("string(.)").strip()

            if len(link.xpath(cells_in_td_xpath)) == 5:
                # Old format (2022 and earlier): single row per case
                # TDs: [citation, materia, docket, name, date, ponente]
                cells = link.xpath(cells_in_td_xpath)
                docket = cells[1].text_content().strip()
                name = cells[2].text_content().strip()
                date_str = cells[3].text_content().strip()
            else:
                # New format (2023+): vertical layout with labeled rows
                # Rows: [Núm., Partes, Ponente, Fecha, Materia]
                cells = link.xpath(cells_in_tr_xpath)
                docket = cells[0].text_content().strip().split("\n")[1]
                name = (
                    re.sub(r"\n+", "\n", cells[1].text_content())
                    .strip()
                    .split("\n")[1]
                )
                date_str = cells[3].xpath(".//td")[1].text_content().strip()

            # "1ro" is Spanish for "primero" (first day of month),
            # which dateparser doesn't recognize
            date_str = re.sub(r"\b1ro\b", "1", date_str)
            date_obj = parse(date_str, languages=["es"])

            date_filed_is_approximate = False
            if not date_obj:
                # E.g. 2022TSPR106 has the docket number in the date
                # column instead of a date due to a website data error
                date_filed_is_approximate = True
                if self.cases:
                    fallback = self.cases[-1]["date"]
                else:
                    fallback = f"{self.year}-01-01"
                logger.info(
                    "Could not parse date for %s, using approximate date %s",
                    citation,
                    fallback,
                )
                parsed_date = fallback
            else:
                parsed_date = str(date_obj.date())

            self.cases.append(
                {
                    "name": name,
                    "url": url,
                    "citation": citation.strip(),
                    "docket": docket,
                    "date": parsed_date,
                    "date_filed_is_approximate": date_filed_is_approximate,
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
