"""Scraper for Supreme Court of Northern Mariana Islands
CourtID: nmi
Court Short Name: NMI
Author: William Edward Palin
History:
  2023-01-21: Created by William Palin
  2026-09-24: Site moved to cnmilaw.gov; use urllib to pass Cloudflare
  2026-10-08: Implement backscraper (#1946)
  2026-10-13: Fix judge names and per curiam (#1946)
"""

import re
from datetime import date
from typing import Any
from urllib.parse import urljoin

from typing_extensions import override

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import normalize_dashes, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    use_urllib = True  # Use urllib to pass Cloudflare
    base_url = "https://cnmilaw.gov/documents?type=case&court=Supreme"
    first_opinion_date = date(1989, 11, 14)

    # Names misspelled or written differently in the listing table.
    # Checked against each opinion's panel in its PDF
    judge_name_fixes = {
        "BELLA": "Bellas",  # 4 N.M.I. 295
        "CABULLIDO": "Carbullido",  # 2014 MP 13
        "CASRTO": "Castro",  # 2002 MP 13
        "CASTRP": "Castro",  # 2001 MP 2
        # The only Torres on the court's panels is Robert J. Torres, Jr. (a
        # Guam justice sitting pro tem, 2005 onward); the listing usually
        # leaves out the "Jr."
        "TORRES": "Torres Jr.",
    }
    # `extract_from_text` looks for a "PER CURIAM" heading in the first
    # `per_curiam_text_limit` characters. Some opinions start after a
    # judgment or an order (2001 MP 11), so the heading can be far down
    per_curiam_text_limit = 6000
    per_curiam_regex = re.compile(r"^[ \t\d\\)|]*PER\s+CURIAM\b", re.MULTILINE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"{self.base_url}&year={date.today().year}"
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        for s in self.html.xpath(".//a[@class='pdf-link']/ancestor::tr"):
            cells = s.xpath(".//td")
            judge_list = self._cleanup_judge_names(cells[3].text_content())
            author = self._fetch_author(judge_list)
            self.cases.append(
                {
                    "name": cells[0].text_content(),
                    # Source renders neutral cites as "YYYY-MP-NN"; eyecite/
                    # reporters-db expect spaces (e.g. "2022 MP 09"). #1947
                    "citation": cells[1].text_content().replace("-", " "),
                    "date": cells[2].text_content(),
                    "judge": ", ".join([j.strip("*") for j in judge_list]),
                    "author": author,
                    # The site doesn't mark every author with "*", so a
                    # missing one doesn't mean per curiam. `extract_from_text`
                    # sets it from the opinion's "PER CURIAM" heading
                    "per_curiam": False,
                    "url": urljoin(
                        self.url, s.xpath(".//a[@class='pdf-link']/@href")[0]
                    ),
                    "docket": "",
                }
            )

    @classmethod
    def _cleanup_judge_names(cls, judges: str) -> list[str]:
        """Clean up the judge panel

        Joins "Jr." to the name it belongs to ("Torres,Jr." -> "Torres Jr."),
        so it isn't split into its own judge, removes the "?" characters
        the source renders in place of unknown ones, and normalizes each name
        with `_normalize_judge_name`. The "*" marking the author is kept, in
        front of the name.

        :param judges: Content of the panel cell
        :return: Judge names list
        """
        judges = re.sub(r"\s*,\s*Jr\.", " Jr.", judges.replace("?", ""))
        names = []
        for judge in judges.split(","):
            if not (name := judge.strip().strip("*").strip()):
                continue
            marker = "*" if "*" in judge else ""
            names.append(f"{marker}{cls._normalize_judge_name(name)}")
        return names

    @staticmethod
    def _fetch_author(judge_names: list[str]) -> str:
        """Parse the author from judge names list

        :param judge_names: Judge names list
        :return: The author, or empty string if no author was found
        """
        authors = [name for name in judge_names if "*" in name]
        if len(authors) > 1:
            logger.warning(
                "nmariana: multiple opinion authors found in %s", judge_names
            )
        if not authors:
            return ""
        return authors[-1].strip("*")

    def extract_from_text(self, scraped_text: str) -> dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: metadata containing the docket number, and the opinion's
            per curiam status when the text has a "PER CURIAM" heading
        """
        normalized_content = normalize_dashes(scraped_text)
        match = re.findall(r"Case No\.: (.*)", normalized_content)
        docket_number = match[0] if match else ""
        metadata = {
            "Docket": {
                "docket_number": docket_number,
            },
        }
        if self._is_per_curiam(scraped_text):
            # The text is more reliable than the listing table, which leaves
            # many authors unmarked and sometimes stars a per curiam opinion
            metadata["Opinion"] = {"author_str": "", "per_curiam": True}
        return metadata

    def _is_per_curiam(self, scraped_text: str) -> bool:
        """Check if the opinion has a "PER CURIAM" heading

        :param scraped_text: Text of the opinion
        :return: True if the opinion is per curiam
        """
        text = scraped_text[: self.per_curiam_text_limit]
        return bool(self.per_curiam_regex.search(text))

    @classmethod
    def _normalize_judge_name(cls, name: str) -> str:
        """Normalize a judge name from the listing table

        :param name: The judge name, without the "*" author marker
        :return: The name from `judge_name_fixes`, or the title cased name
        """
        return cls.judge_name_fixes.get(name.upper()) or titlecase(
            name.lower()
        )

    @override
    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Build the list of years to backscrape, both ends inclusive

        :param kwargs: passed when initializing the scraper; may contain
            `backscrape_start` and `backscrape_end` as "YYYY" strings
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")
        start = int(start) if start else self.first_opinion_date.year
        end = int(end) if end else date.today().year
        self.back_scrape_iterable = list(range(start, end + 1))

    @override
    async def _download_backwards(self, year: int) -> None:
        logger.info("Backscraping for year %s", year)
        self.url = f"{self.base_url}&year={year}"
        self.html = await self._download()
        self._process_html()
