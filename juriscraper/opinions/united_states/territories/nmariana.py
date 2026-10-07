"""Scraper for Supreme Court of Northern Mariana Islands
CourtID: nmi
Court Short Name: NMI
Author: William Edward Palin
History:
  2023-01-21: Created by William Palin
  2026-09-24: Site moved to cnmilaw.gov; use urllib to pass Cloudflare
  2026-10-07: Implement backscraper (#1946)
"""

import re
from datetime import date
from typing import Any
from urllib.parse import urljoin

from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.Backscraper import YearBackscraper
from juriscraper.lib.string_utils import normalize_dashes
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(YearBackscraper, OpinionSiteLinear):
    use_urllib = True  # Use urllib to pass Cloudflare
    base_url = "https://cnmilaw.gov/documents?type=case&court=Supreme"
    first_opinion_date = date(1989, 11, 14)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"{self.base_url}&year={date.today().year}"
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    def _cleanup_judge_names(self, judges: str) -> list[str]:
        """Extract judge panel

        Because of a judge Torres,Jr. - and the various permutations of his
        Jr with and without commas and spacing we do a bit of cleanup to
        get his and the other judges corretly.  Additionally the author is
        sometimes denoted by a *.  This is cleaned up.

        :param judges: Content of the panel as a string
        :return: Judges as a string list
        """
        judge_list = judges.split(",")
        judge_list = [j.replace(" Jr.", "Jr.").strip(" *") for j in judge_list]
        judge_list = [j.replace("Jr.", " Jr.") for j in judge_list]
        return judge_list

    def _fetch_author(self, judges: str) -> str:
        """Parse the author from the judge text

        :param judges: Cell content
        :return: The author
        """
        if "*" not in judges:
            author = ""
        else:
            author = [j for j in judges.split(",") if "*" in j][0].strip("*")
        return author

    @override
    def _process_html(self) -> None:
        for s in self.html.xpath(".//a[@class='pdf-link']/ancestor::tr"):
            cells = s.xpath(".//td")
            judge_text = cells[3].text_content()
            author = self._fetch_author(judge_text)
            self.cases.append(
                {
                    "name": cells[0].text_content(),
                    # Source renders neutral cites as "YYYY-MP-NN"; eyecite/
                    # reporters-db expect spaces (e.g. "2022 MP 09"). #1947
                    "citation": cells[1].text_content().replace("-", " "),
                    "date": cells[2].text_content(),
                    "judge": ", ".join(self._cleanup_judge_names(judge_text)),
                    "author": author,
                    "per_curiam": not author,
                    "url": urljoin(
                        self.url, s.xpath(".//a[@class='pdf-link']/@href")[0]
                    ),
                    "docket": "",
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: metadata containing the docket number
        """
        normalized_content = normalize_dashes(scraped_text)
        match = re.findall(r"Case No\.: (.*)", normalized_content)
        docket_number = match[0] if match else ""
        metadata = {
            "Docket": {
                "docket_number": docket_number,
            },
        }
        return metadata

    @override
    async def _download_backwards(self, year: int) -> None:
        logger.info("Backscraping for year %s", year)
        self.url = f"{self.base_url}&year={year}"
        self.html = await self._download()
        self._process_html()
