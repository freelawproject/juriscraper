"""
Scraper for Indiana Supreme Court
CourtID: ind
Court Short Name: Ind.
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-03: Created by Jon Andersen
    2025-07-09: Updated bt luism add new fields for lower court details and judge names
"""

from juriscraper.lib.type_utils import OpinionType
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    page_court_id = "9510"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "Supreme Court"
        self.status = "Published"
        self.url = f"https://public.courts.in.gov/Decisions/api/Search?courtId={self.page_court_id}"
        self.should_have_results = True

    def _process_html(self):
        for case in self.html:
            is_per_curiam = case["opinion"]["perCuriam"]
            other_courts = [
                c for c in case["courts"] if c["name"] != self.court_name
            ]

            disposition = case["decision"]
            if disposition == "Opinion Issued":
                disposition = ""

            judge = ", ".join(
                self.clean_judge_name(v["judge"])
                for v in case["opinion"]["votes"]
            )

            type = (
                OpinionType.MAJORITY.value
                if "Majority Opinion" in (case["opinion"].get("result") or "")
                else ""
            )

            self.cases.append(
                {
                    "name": case["style"],
                    "docket": case["caseNumber"],
                    "date": case["date"],
                    "url": f"https://public.courts.in.gov/Decisions/{case['opinionUrl']}",
                    "disposition": disposition,
                    "lower_court": ", ".join(c["name"] for c in other_courts),
                    "lower_court_number": ", ".join(
                        c["number"] for c in other_courts
                    ),
                    "judge": judge,
                    "author": self.extract_author(case, is_per_curiam),
                    "per_curiam": is_per_curiam,
                    "type": type,
                }
            )

    @staticmethod
    def clean_judge_name(name: str) -> str:
        """Cleans and formats a judge's name string."""

        parts = name.split(", ")
        if len(parts) < 2:
            return parts[0]

        result = parts[0]
        if "SR" in parts[1]:
            result += " SR"
        elif len(parts) > 2:
            result += f" {parts[2]}"

        return result

    @staticmethod
    def extract_author(case: dict, is_per_curiam: bool) -> str:
        """Extracts and cleans the author field from the case data."""
        if is_per_curiam:
            return ""
        return (
            case["opinionText"]
            .replace("in an opinion by ", "")
            .replace(".", "")
        )
