# Scraper for the United States Court of Appeals for the Seventh Circuit
# CourtID: ca7
# Court Short Name: 7th Cir.

import re

import feedparser

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://media.ca7.uscourts.gov/cgi-bin/OpinionsWeb/processWebInputExternal.pl?Time=month&startDate=&endDate=&Author=any&AuthorName=&Case=any&CaseYear=&CaseNum=&Rubmit=RssRecent&RssJudgeName=Sykes&OpsOnly=yes"
        self.should_have_results = True
        self.court_id = self.__module__

    def _process_html(self):
        if self.test_mode_enabled():
            self.year = 2022
        feed = feedparser.parse(self.request["response"].content)
        for item in feed["entries"]:
            if item.get("published_parsed", None) is None:
                logger.warning("Skipping item with no published date")
                continue
            parts = item["summary"].split()
            docket = parts[parts.index("case#") + 1]
            name = item["summary"].split(docket)[1].split("(")[0]
            author = item["summary"].split("{")[1].split("}")[0]
            date = item["published"]
            per_curiam = False
            if "curiam" in author.lower():
                per_curiam = True
                author = ""

            self.cases.append(
                {
                    "url": item["link"],
                    "docket": docket,
                    "date": date,
                    "name": name,
                    "status": "Published",
                    "judge": author,
                    "author": author,
                    "per_curiam": per_curiam,
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"""
            (?:
               Appeals?\s+from\s+the\s+
           | (?:On\s+)?Petitions?\s+for\s+Review\s+of\s+(?:an\s+)?Orders?\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*(?:\.|Nos?\.|USDC))
            """,
            re.X,
        )

        lower_court = ""
        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

        if lower_court:
            return {
                "Docket": {
                    "appeal_from_str": lower_court,
                }
            }
        return {}
