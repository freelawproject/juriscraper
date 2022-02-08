# Author: Phil Ardery
# Date created: 2017-01-27
# Contact: 501-682-9400 (Administrative Office of the Curt)

import datetime
import re
from typing import Any, Dict

import feedparser

from juriscraper.lib.string_utils import normalize_dashes, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    """This scraper has an intential 10 opinion limit to avoid lexum cap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "supremecourt"
        self.url = f"https://opinions.arcourts.gov/ark/{self.court}/en/rss.do"
        self.year = datetime.date.today().year
        self.cite_regex = r"\d{2,4} Ark\. \d+"

    def _process_html(self) -> None:
        feed = feedparser.parse(self.request["response"].content)
        for item in feed["entries"]:
            if not re.findall(self.cite_regex, item["title"], re.I | re.M):
                continue

            name, cite, date = item["title"].split("\n")
            name = titlecase(name.strip(" -"))
            cite = cite.strip(" -")
            date = date.strip(" -")

            if int(date[-4:]) != self.year:
                # The RSS feed has the most recent opinions and then dozens from the 1960's.  Not sure why
                # but we dont want to collect those.
                continue
            if len(self.cases) >= 10:
                # Limit to max of 10 cases per crawl to stay under limit.
                # We assume it is the same for NM (lexum) at 50/min 100/5min
                continue
            doc_id = re.findall(r"\d{4,}", item["link"])[0]
            url = f"https://opinions.arcourts.gov/ark/{self.court}/en/{doc_id}/1/document.do"
            self.cases.append(
                {
                    "date": date,
                    "docket": "",
                    "name": name,
                    "citation": cite,
                    "url": url,
                    "status": "Published",
                }
            )

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: metadata
        """
        normalized_content = normalize_dashes(scraped_text)
        match = re.findall(r"No\. (\w+-\d+-\d+)", normalized_content)
        docket_number = match[0] if match else ""
        metadata = {
            "OpinionCluster": {
                "docket_number": docket_number,
            },
        }
        return metadata
