"""Scraper for the Supreme Court of Michigan
CourtID: mich
Court Short Name: Mich.
Contact: sitefeedback@courts.mi.gov
History:
    - 2014-09-21: Updated by Jon Andersen to handle some fields being missing
    - 2014-08-05: Updated to have a dynamic URL, an oversight during check in.
    - 2022-01-28: Updated for new web site, @satsuki-chan.
"""

import re
from urllib.parse import urlencode, urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    title_re = re.compile(
        r"(MSC|COA) (?P<docket>\d{6})\s+(?P<name>.+)\s+Opinion"
    )
    court = "Supreme Court"
    filters = (
        ("releaseDate", "Past Year"),
        ("page", "1"),
        ("sortOrder", "Newest"),
        ("searchQuery", ""),
        ("resultType", "opinions"),
        ("pageSize", "100"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        params = self.filters + (
            ("resource", "supreme-court-opinion"),
            ("aAppellateCourt", self.court),
        )
        self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?{urlencode(params)}"
        # Currently blocked from Michigan so we drop the user agent for now
        self.request["headers"] = {"User-Agent": ""}

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for item in self.html["searchItems"]:
            if match := self.title_re.search(item["title"]):
                docket = match.group("docket")
                name = self.cleanup_case_name(match.group("name"))
            else:
                name, docket = self.get_missing_name_and_docket(item)

            disposition = self.get_disposition(item)

            status = "Published"
            if "Unpublished" in item["title"]:
                status = "Unpublished"

            per_curiam = False
            if "per curiam" in item["title"].lower():
                per_curiam = True

            self.cases.append(
                {
                    "date": item["filingDate"],
                    "docket": docket,
                    "name": name,
                    "url": urljoin(self.url, item["documentUrl"].strip()),
                    "lower_court": self.parse_lower_courts(item["courts"]),
                    "status": status,
                    "per_curiam": per_curiam,
                    "disposition": disposition,
                }
            )

    def cleanup_case_name(self, name_raw: str) -> str:
        """Clean up case name in Michigan

        :param name_raw: Raw title string
        :return: Cleaned name
        """
        name = titlecase(re.sub(r"\s+", " ", name_raw.strip()))
        return name.replace("People of Mi ", "People of Michigan ")

    def parse_lower_courts(self, courts: list[str]) -> str:
        """Get the lower courts

        :param courts: Court names as an array
        :return: The lower courts combined into a string
        """
        lower_courts = re.sub(r"\s+", " ", ", ".join(courts).lstrip(", "))
        return titlecase(lower_courts)

    def get_missing_name_and_docket(self, item: dict) -> tuple[str, str]:
        """
        Return 2 placeholders. We can get the values via `extract_from_text`
        To be overriden in `michctapp`
        Sometimes the API returns bad "title" values. See #1648
        """
        return "Placeholder case name", "Placeholder docket number"

    def get_disposition(self, item: dict) -> str:
        """To be overriden by michctapp"""
        return ""

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extracts case names and docket numbers from the document's text

        :param scraped_text: the document's text
        :return: a dictionary in the shape of Courtlistener's models
        """
        pattern = re.compile(
            r"(?P<case_name>([\S ]+\n)+)\n+\s+Docket Nos?. (?P<docket_number>(\d{6}(,? and |, |.)?)+)"
        )
        if match := pattern.search(scraped_text[:1500]):
            docket_number = match.group("docket_number").strip(" .")
            name = self.cleanup_case_name(
                match.group("case_name").replace("\n", ";")
            ).strip("; ")
            return {
                "OpinionCluster": {"case_name": name},
                "Docket": {"case_name": name, "docket_number": docket_number},
            }
        else:
            logger.error(
                "mich: extract_from_text failed",
                extra={"opinion_text": scraped_text[:1024].strip()},
            )
            return {}
