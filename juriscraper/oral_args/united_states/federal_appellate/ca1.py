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

from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

        self.url = "http://www.ca1.uscourts.gov/doarrss/feed"

    def _process_html(self) -> None:
        """Process the RSS feed.

        Iterate over each item in the RSS feed to extract out
        the date, case name, docket number, and status and pdf URL.
        Return: None
        """
        feed = feedparser.parse(self.request["response"].content)
        for item in feed["entries"]:
            self.cases.append(
                {
                    "date": item["published"].split()[0],
                    "url": item["link"],
                    "status": "Unknown",
                    "docket": item["id"].split(" ", 2)[1].strip(","),
                    "name": item["id"].split(" ", 2)[2],
                }
            )
