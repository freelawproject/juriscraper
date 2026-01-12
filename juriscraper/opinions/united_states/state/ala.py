"""
Scraper for Alabama Supreme Court
CourtID: ala
Court Short Name: Alabama
Author: William Palin
Court Contact:
History:
 - 2023-01-04: Created.
 - 2023-011-14: Alabama no longer uses page or use selenium.
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
        self.url = f"{self.base_url}/courts/cms/publications?courtID={self.court_str}&page=0&size=25&sort=publicationDate%2Cdesc"
        self.should_have_results = True

    def _download(self, request_dict=None):
        """Download the publication list and then fetch detailed publication data.

        The initial API returns a list of publications, but we need to fetch
        the detailed publication endpoint to get full case information.
        """
        if self.test_mode_enabled():
            return super()._download(request_dict)

        # First, get the list of publications
        html = super()._download(request_dict)

        # Get the publicationUUID from the initial response
        releases = html["_embedded"]["results"]
        publication_uuid = releases[0].get("publicationUUID")

        # Fetch detailed publication data
        self.url = f"{self.base_url}/courts/{self.court_str}/cms/publication/{publication_uuid}"
        return super()._download(request_dict)

    def _process_html(self):
        item = self.html

        date_filed = item["publicationDate"][:10]
        for publicationItem in item["publicationItems"]:
            if not publicationItem.get("documents", []):
                continue

            url = "{}/courts/{}/cms/case/{}/docketentrydocuments/{}".format(
                self.base_url,
                self.court_str,
                publicationItem["caseInstanceUUID"],
                publicationItem["documents"][0]["documentLinkUUID"],
            )
            docket = publicationItem["caseNumber"]
            name = publicationItem["title"]

            lower_court = ""
            lower_court_number = ""

            # Match either:
            # 1. (Appeal from <court>: <number>) - standard appeals
            # 2. (<Court>: <num>; <Appeals>: <num>) - Ex parte cases (extract Appeals court)
            match = re.search(
                r"\((?:Appeal from ([^:]+):\s*([^)]+)|[^;]+;\s*([^:]+Appeals):\s*([^)]+))\)",
                name,
            )
            if match:
                # Groups 1,2 for "Appeal from"; groups 3,4 for Ex parte format
                lower_court = (match.group(1) or match.group(3) or "").strip()
                lower_court_number = (
                    match.group(2) or match.group(4) or ""
                ).strip()
                if match.group(1):
                    # "Appeal from" format - just remove the parenthetical
                    name = name[: match.start()].rstrip()
                else:
                    # Ex parte format - clean up the full case name
                    name = re.sub(
                        r"\s*PETITION FOR WRIT OF .+?(?=\(|$)", "", name
                    ).strip()
                    name = re.sub(r"\s*\(In re:\s*.+?\)", "", name).strip()
                    name = re.sub(
                        r"\s*\([^)]+Court[^)]+\)\.*", "", name
                    ).strip()
                    name = name.rstrip(".")

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
