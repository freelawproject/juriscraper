"""
History:
    - 2014-08-05: Updated by mlr because it was not working, however, in middle
      of update, site appeared to change. At first there were about five
      columns in the table and scraper was failing. Soon, there were seven and
      the scraper started working without my fixing it. Very odd.
    - 2023-01-13: Update to use RSS Feed
    - 2025-08-27: Added extract_from_text and avoid duplicates.
    - 2026-05-29: Updated URL after site moved feeds under /decisions/.
"""

import re

import feedparser
from lxml.html import HtmlElement, tostring
from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import ExtractedMetadata, RawOpinion
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Entry(TypedDict):
    title: str
    link: str
    published: str


_entries_adapter = TypeAdapter(list[_Entry])


class Site(OpinionSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca9.uscourts.gov/decisions/opinions/index.xml"
        self.status = "Published"
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        feed = feedparser.parse(tostring(self.html))
        for item in _entries_adapter.validate_python(
            feed.entries, strict=True
        ):
            case: RawOpinion = {
                "name": titlecase(item["title"]),
                "url": item["link"],
                "date": item["published"],
                "status": self.status,
                "docket": item["link"].split("/")[-1][:-4],
            }
            # Avoid duplicates cases from source page
            if case not in self.cases:
                self.cases.append(case)

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
              | On\s+Remand\s+from\s+the\s+
              | On\s+Petition\s+for\s+Review\s+of\s+an\s+Order\s+of\s+the\s+
            )
            (?P<lower_court>.+(?:\n.+)?)
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
