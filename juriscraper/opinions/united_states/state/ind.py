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

from typing import NotRequired

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Vote(TypedDict):
    judge: str


class _Opinion(TypedDict):
    votes: list[_Vote]
    perCuriam: bool


class _Court(TypedDict, total=False):
    id: int
    name: str
    number: str


class _Case(TypedDict):
    decision: str
    opinion: _Opinion
    opinionText: str
    style: str
    caseNumber: str
    date: str
    opinionUrl: str
    courts: NotRequired[list[_Court]]


_cases_adapter = TypeAdapter(list[_Case])


class Site(OpinionSiteLinear):
    page_court_id = "9510"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.court_name = "Supreme Court"
        self.status = "Published"
        self.url = f"https://public.courts.in.gov/Decisions/api/Search?courtId={self.page_court_id}"
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        """Process the HTML to extract case details.

        :return None
        """
        for case in _cases_adapter.validate_python(self.html, strict=True):
            lower_court, lower_court_number = self.parse_court_info(case)

            disposition = case["decision"]
            if disposition == "Opinion Issued":
                disposition = ""

            judge = ", ".join(
                self.clean_judge_name(v["judge"])
                for v in case["opinion"]["votes"]
            )

            per_curiam = case["opinion"]["perCuriam"]
            author = (
                (
                    case["opinionText"]
                    .replace("in an opinion by ", "")
                    .replace(".", "")
                )
                if not per_curiam
                else ""
            )

            self.cases.append(
                {
                    "name": case["style"],
                    "docket": case["caseNumber"],
                    "date": case["date"],
                    "url": f"https://public.courts.in.gov/Decisions/{case['opinionUrl']}",
                    "disposition": disposition,
                    "lower_court": lower_court,
                    "lower_court_number": lower_court_number,
                    "judge": judge,
                    "author": author,
                    "per_curiam": per_curiam,
                }
            )

    @staticmethod
    def clean_judge_name(name: str) -> str:
        """Cleans and formats a judge's name string.

        :param name: The name of the judge as a string.
        :return: A cleaned and formatted version of the judge's name.
        """

        parts = name.split(", ")
        if len(parts) < 2:
            return parts[0]

        result = parts[0]
        if "SR" in parts[1]:
            result += " SR"
        elif len(parts) > 2:
            result += f" {parts[2]}"

        return result

    def parse_court_info(self, case: _Case) -> tuple[str, str]:
        """Extract the lower court name and number from case data

        :param case: case row json to parse
        :return: lower court data
        """
        excluded = {self.court_name}
        if self.court_name == "Court of Appeals":
            excluded.add("Supreme Court")

        # Filter out excluded courts
        courts = [
            c for c in case.get("courts", []) if c.get("name") not in excluded
        ]
        if not bool(courts):
            return "", ""

        # Pick the court with the largest ID
        target = max(courts, key=lambda c: c.get("id", 0))
        name = target.get("name", "")
        number = target.get("number", "")

        # Normalize specific court names
        normalization = {
            "Court of Appeals": "Indiana Court of Appeals",
            "Tax Court": "Indiana Tax Court",
        }
        return normalization.get(name, name), number
