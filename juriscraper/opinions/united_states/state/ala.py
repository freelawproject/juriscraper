"""
Scraper for Alabama Supreme Court
CourtID: ala
Court Short Name: Alabama
Author: William Palin
Court Contact:
History:
 - 2023-01-04: Created.
 - 2023-011-14: Alabama no longer uses page or use selenium.
"""

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_str = "68f021c4-6a44-4735-9a76-5360b2e8af13"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"https://publicportal-api.alappeals.gov/courts/cms/publications?courtID={self.court_str}&page=0&size=25&sort=publicationDate%2Cdesc"
        self.should_have_results = True

    def _process_html(self):
        self.json = self.html

        # Processes only the first result to scrape the most recent data.
        item = self.json["_embedded"]["results"][0]

        date_filed = item["scheduledDate"][:10]
        for publicationItem in item["publicationItems"]:
            if not publicationItem.get("documents", []):
                continue

            url = f"https://publicportal-api.alappeals.gov/courts/{self.court_str}/cms/case/{publicationItem['caseInstanceUUID']}/docketentrydocuments/{publicationItem['documents'][0]['documentLinkUUID']}"
            docket = publicationItem["caseNumber"]
            name = publicationItem["title"]

            lower_court = ""
            lower_court_number = ""
            # Regex to match: (Appeal from <court>: <number>) or (Appeal from <court>: <number> and <number>)
            match = re.search(
                r"\(Appeal from (?P<lower_court>.+?): (?P<lower_court_number>.+?)\)",
                name,
            )
            if match:
                lower_court = match.group("lower_court").strip()
                lower_court_number = match.group("lower_court_number").strip()
                # Remove the parenthetical from the name
                name = name[: match.start()].rstrip()

            judge = publicationItem["groupName"]
            if judge == "On Rehearing":
                judge = ""

            per_curiam = False
            if "curiam" in judge.lower():
                judge = ""
                per_curiam = True

            self.cases.append(
                {
                    "date": date_filed,
                    "name": name,
                    "docket": docket,
                    "status": "Published",
                    "url": url,
                    "judge": judge,
                    "per_curiam": per_curiam,
                    "lower_court": lower_court,
                    "lower_court_number": lower_court_number,
                }
            )
