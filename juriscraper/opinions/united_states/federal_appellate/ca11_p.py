# Editor: mlr
# Maintenance log
#    Date     | Issue
# 2013-01-28  | InsanityException due to the court adding busted share links.
# 2014-07-02  | New website required rewrite.
# 2025-08-26  | Updated to use OpinionSiteLinear and added extract_from_text.

import re

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, clean_string
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[int]):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "http://media.ca11.uscourts.gov/opinions/pub/logname.php"
        self.back_scrape_iterable = list(range(20, 10000, 20))
        self.should_have_results = True
        self.status = "Published"

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//tr")
        for row in rows:
            # Extract values from each <td> in the row
            tds = row.findall("td")
            if len(tds) < 5:
                continue  # Skip rows that don't have enough columns

            name: str = tds[0].xpath("a//text()")[0]
            url: str = tds[0].xpath("a/@href")[0]
            docket: str = tds[1].xpath(".//text()")[0]
            lower_court_docket: str = tds[2].xpath(".//text()")[0]
            nature: str = tds[3].xpath(".//text()")[0]
            date: str = tds[4].xpath(".//text()")[0]

            s = clean_string(date)
            if s == "00-00-0000" and "begin=21160" in (
                self.url if self.url is not None else ""
            ):
                s = "12-13-2006"
            date_cleaned = clean_string(s)

            self.cases.append(
                {
                    "name": clean_string(name),
                    "url": url,
                    "date": date_cleaned,
                    "docket": clean_string(docket),
                    "lower_court_number": lower_court_docket,
                    "nature_of_suit": clean_string(nature),
                }
            )

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"""
            (?:
               Appeals?\s+from\s+the\s+
              | Petitions?\s+for\s+Review\s+of\s+(?:a\s+)?Decision\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*(?:\.|Nos?\.|USC|D.C.))
            """,
            re.X,
        )

        lower_court = ""
        if (match := pattern.search(scraped_text)) is not None:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

        if bool(lower_court):
            return {
                "Docket": {
                    "appeal_from_str": lower_court,
                }
            }

        return {}

    @override
    async def _download_backwards(self, n: int) -> None:
        self.url = f"http://media.ca11.uscourts.gov/opinions/pub/logname.php?begin={n}&num={n / 20 - 1}&numBegin=1"
        self.html = await self._download()
        self._process_html()
