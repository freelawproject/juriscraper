"""
Scraper for Alabama Supreme Court
CourtID: ala
Court Short Name: Alabama
Author: William Palin
Court Contact:
History:
 - 2023-01-04: Created.
 - 2023-11-14: Alabama no longer uses page or use selenium.
 - 2026-01-12: fetch detailed publication data from new API endpoint.
"""

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_str = "68f021c4-6a44-4735-9a76-5360b2e8af13"
    base_url = "https://publicportal-api.alappeals.gov"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"{self.base_url}/courts/cms/publications"
        self.request["parameters"]["params"] = {
            "courtID": self.court_str,
            "page": 0,
            "size": 25,
            "sort": "publicationDate,desc",
        }
        self.should_have_results = True

    def _download(self, request_dict=None):
        """Download the publication list and then fetch detailed publication data.

        The initial API returns a list of publications, but we need to fetch
        the detailed publication endpoint to get full case information.
        """
        if self.test_mode_enabled():
            self.json =  super()._download(request_dict)
            return

        # First, get the list of publications
        resp = super()._download(request_dict)

        # Get the publicationUUID from the initial response
        releases = resp["_embedded"]["results"]
        publication_uuid = releases[0].get("publicationUUID")

        # Fetch detailed publication data (no params needed for this endpoint)
        self.url = f"{self.base_url}/courts/{self.court_str}/cms/publication/{publication_uuid}"
        self.request["parameters"]["params"] = {}
        self.json = super()._download(request_dict)

    def _process_html(self):
        date_filed = self.json["publicationDate"][:10]
        for publicationItem in self.json["publicationItems"]:
            if not publicationItem.get("documents", []):
                continue

            name = publicationItem["title"]

            # Skip petition cases
            if "PETITION FOR WRIT" in name:
                continue

            url = "{}/courts/{}/cms/case/{}/docketentrydocuments/{}".format(
                self.base_url,
                self.court_str,
                publicationItem["caseInstanceUUID"],
                publicationItem["documents"][0]["documentLinkUUID"],
            )
            docket = publicationItem["caseNumber"]

            lower_court = ""
            lower_court_number = ""

            # Match (Appeal from <court>: <number>) format for standard appeals
            match = re.search(
                r"\(Appeal from (?P<lower_court>[^:]+):\s*(?P<lower_court_number>[^)]+)\)",
                name,
            )
            if match:
                lower_court = match.group("lower_court").strip()
                lower_court_number = match.group("lower_court_number").strip()
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
