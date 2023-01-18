# Scraper for the United States Court of Appeals for the Seventh Circuit
# CourtID: ca7
# Court Short Name: 7th Cir.

import feedparser

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://media.ca7.uscourts.gov/cgi-bin/OpinionsWeb/processWebInputExternal.pl?Time=month&startDate=&endDate=&Author=any&AuthorName=&Case=any&CaseYear=&CaseNum=&Rubmit=RssRecent&RssJudgeName=Sykes&OpsOnly=yes"
        self.court_id = self.__module__

    def _process_html(self):
        if self.test_mode_enabled():
            self.year = 2022
        feed = feedparser.parse(self.request["response"].content)
        for item in feed["entries"]:
            parts = item["summary"].split()
            docket = parts[parts.index("case#") + 1]
            name = item["summary"].split(docket)[1].split("(")[0]
            self.cases.append(
                {
                    "url": item["link"],
                    "docket": docket,
                    "date": item["published"],
                    "name": name,
                    "status": "Published",
                    "author": item["summary"].split("{")[1].split("}")[0],
                }
            )
