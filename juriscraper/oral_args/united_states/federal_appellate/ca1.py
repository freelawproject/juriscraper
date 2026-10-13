"""Scraper for First Circuit of Appeals
CourtID: ca1
Court Short Name: ca1
Author: Michael Lissner
Date created: 13 June 2014
History:
- 2014-06-13: Created by mlr
- 2022-09-20: Updated by flooie
"""

import feedparser
from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class _Entry(TypedDict):
    published: str
    link: str
    id: str


_entries_adapter = TypeAdapter(list[_Entry])


class Site(OralArgumentSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__

        self.url = "http://www.ca1.uscourts.gov/doarrss/feed"

    @override
    def _process_html(self) -> None:
        """Process the RSS feed.

        Iterate over each item in the RSS feed to extract out
        the date, case name, docket number, and status and pdf URL.
        Return: None
        """
        response = self.request.get("response")
        if response is None:
            raise ValueError("Download a response before accessing it.")
        feed = feedparser.parse(response.content)
        for item in _entries_adapter.validate_python(
            feed.entries, strict=True
        ):
            self.cases.append(
                {
                    "date": item["published"].split()[0],
                    "url": item["link"],
                    "docket": item["id"].split(" ", 2)[1].strip(","),
                    "name": item["id"].split(" ", 2)[2],
                }
            )
