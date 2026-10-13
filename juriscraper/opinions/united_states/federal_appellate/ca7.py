# Scraper for the United States Court of Appeals for the Seventh Circuit
# CourtID: ca7
# Court Short Name: 7th Cir.

import re

import feedparser
from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Entry(TypedDict):
    summary: str
    published: str
    link: str


_entry_adapter = TypeAdapter(_Entry)


class Site(OpinionSiteLinear):
    year: int

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = "https://media.ca7.uscourts.gov/cgi-bin/OpinionsWeb/processWebInputExternal.pl?Time=month&startDate=&endDate=&Author=any&AuthorName=&Case=any&CaseYear=&CaseNum=&Rubmit=RssRecent&RssJudgeName=Sykes&OpsOnly=yes"
        self.should_have_results = True
        self.court_id = self.__module__

    @override
    def _process_html(self) -> None:
        if self.test_mode_enabled():
            self.year = 2022
        response = self.request.get("response")
        if response is None:
            raise ValueError("Download a response before accessing it.")
        feed = feedparser.parse(response.content)
        for raw_item in feed.entries:
            if raw_item.get("published_parsed") is None:
                logger.warning("Skipping item with no published date")
                continue
            item = _entry_adapter.validate_python(raw_item, strict=True)
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
           | (?:On\s+)?Petitions?\s+for\s+Review\s+of\s+(?:an\s+)?Orders?\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*(?:\.|Nos?\.|USDC))
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
