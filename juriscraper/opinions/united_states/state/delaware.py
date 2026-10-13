"""Scraper for the Supreme Court of Delaware
CourtID: del

Creator: Andrei Chelaru
Reviewer: mlr
"""

import re
from urllib.parse import urljoin

from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import ExtractedMetadata, RawOpinion
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.url = (
            "https://courts.delaware.gov/opinions/List.aspx?ag=supreme%20court"
        )
        # Note that we can't do the usual thing here because 'del' is a Python keyword.
        self.court_id = "juriscraper.opinions.united_states.state.del"
        self.should_have_results = True
        self.status = "Published"

    @override
    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//table//tr[not(th)]")
        for row in rows:
            url: str = row.xpath("td[1]/a/@href")[0].strip()
            case: RawOpinion = {
                "name": row.xpath("td[1]/a/text()")[0].strip(),
                "date": row.xpath("td[2]/span/text()")[0].strip(),
                "docket": row.xpath("td[3]/span/text()")[0].strip(),
                "url": urljoin(
                    (self.url if self.url is not None else ""),
                    url,
                ),
                "judge": " ".join(row.xpath("td[6]/text()")).strip(),
                "per_curiam": False,
            }
            if (
                "per curiam"
                in (
                    judge_value
                    if (judge_value := case.get("judge")) is not None
                    else ""
                ).lower()
            ):
                case["judge"] = ""
                case["per_curiam"] = True

            self.cases.append(case)

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """

        cleaned_text = "\n".join(
            line.rsplit("§", 1)[-1] if "§" in line else line
            for line in scraped_text[:1500].splitlines()
        )

        pattern = re.compile(
            r"Court\s+Below[–—\-:]\s*(?:the\s+)?(?P<lower_court>.*?)\n\s*\n",
            re.X | re.IGNORECASE | re.DOTALL,
        )

        number_pattern = re.compile(
            r"Nos?\.:?\s*(?P<lower_court_number>\S{5,})(?:\s|\()",
            re.IGNORECASE,
        )

        result: ExtractedMetadata = {}

        if (match := pattern.search(cleaned_text)) is not None:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            result["Docket"] = {"appeal_from_str": lower_court}

            if (
                number_match := number_pattern.search(cleaned_text)
            ) is not None:
                lower_court_number = number_match.group(
                    "lower_court_number"
                ).strip()
                result["OriginatingCourtInformation"] = {
                    "docket_number": lower_court_number
                }

        return result
