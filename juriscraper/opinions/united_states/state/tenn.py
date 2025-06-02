"""
Scraper for the Supreme Court of Tennessee
CourtID: tenn
Court Short Name: Tenn.
"""

import re
from typing import Optional

from juriscraper.lib.type_utils import (
    CONCURRENCE,
    CONCURRING_IN_PART_AND_DISSENTING_IN_PART,
    DISSENT,
    MAJORITY,
    types_mapping,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.tncourts.gov/courts/supreme-court/opinions"
        self.court_id = self.__module__
        self.status = "Unknown"

    def _process_html(self):
        """
        Parse the HTML table rows and extract case details.

        Iterates over each table row in the HTML, extracting the date, URL, case name,
        docket number, judge, lower court judge, summary, per curiam status, and opinion type.
        Appends a dictionary with these details to self.cases.
        """
        for row in self.html.xpath("//tr"):
            date = (
                row.xpath(
                    ".//td[contains(@class, 'views-field-field-opinions-date-filed')]"
                )[0]
                .text_content()
                .strip()
            )
            section = row.xpath(
                ".//td[contains(@class, 'views-field-field-opinions-case-number')]"
            )[0]
            url = section.xpath(".//a")[0].get("href")

            name_text = section.xpath(".//a")[0].text_content()
            type_match = re.search(r"\(([^)]+)\)", name_text)
            type_raw = type_match.group(1).lower() if type_match else ""

            opinion_type = self.extract_type(type_raw)

            name = re.sub(r"\s*\([^)]+\)", "", name_text).strip()
            rows = [
                row.strip()
                for row in section.text_content().strip().split("\n", 4)
            ]

            judge = (
                rows[2].split(": ")[1] if "judge" in rows[2].lower() else ""
            )
            lower_court_judge = (
                rows[3].split(": ")[1] if "judge" in rows[3].lower() else ""
            )
            summary = rows[-1] if "Judge" not in rows[-1] else ""
            per_curiam = False
            if "curiam" in judge.lower():
                judge = ""
                per_curiam = True

            self.cases.append(
                {
                    "date": date,
                    "url": url,
                    "name": name,
                    "docket": rows[1],
                    "judge": judge,
                    "lower_court_judge": lower_court_judge,
                    "summary": summary,
                    "per_curiam": per_curiam,
                    "type": opinion_type,
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract precedential_status and appeal_from_str from scraped text.

        :param scraped_text: Text of the scraped content
        :return: dictionary with precedential_status and appeal_from_str
        """
        lower_court = self.extract_court_name(scraped_text)
        precedential_status = (
            "Published"
            if "MEMORANDUM OPINION" not in scraped_text
            else "Unpublished"
        )
        result = {
            "OpinionCluster": {"precedential_status": precedential_status}
        }
        if lower_court:
            result["Docket"] = {"appeal_from_str": lower_court}
        return result

    def extract_court_name(self, text: str) -> Optional[str]:
        patterns = [
            (
                r"Appeal by Permission from the\s+(Court of (?:Appeals|Criminal Appeals))(?:\s*\n?\s*)+((?:Chancery|Circuit|Criminal) Court for \w+(?:\s+\w+)* County)",
                lambda m: f"{m.group(1)} {m.group(2)}",
            ),
            (
                r"Direct Appeal from the\s+((?:Chancery|Circuit|Criminal) Court for \w+(?:\s+\w+)* County)",
                lambda m: m.group(1),
            ),
            (
                r"Appeal from the\s+((?:Chancery|Circuit|Criminal|General Sessions|Juvenile) Court for \w+(?:\s+\w+)* County|\w+(?:\s+\w+)* County (?:Chancery|Circuit|Criminal|General Sessions) Court|Juvenile)",
                lambda m: m.group(1),
            ),
            (
                r"Appeal by Permission from the\s+(Court of (?:Appeals|Criminal Appeals))(?!\s*(?:Chancery|Circuit|Criminal))",
                lambda m: m.group(1),
            ),
            (
                r"^(?!.*(?:Appeal by Permission from|Direct Appeal from|Appeal from)).*?((?:Chancery|Circuit|Criminal) Court for \w+(?:\s+\w+)* County)",
                lambda m: m.group(1),
            ),
        ]
        for pattern, handler in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                return handler(match)
        return None

    def extract_type(self, type_raw: str) -> str:
        """
        Map a raw opinion type string to a standardized type.

        :param type_raw: Raw type string extracted from the opinion (e.g., 'concurring', 'dissenting')
        :return: Standardized type string from types_mapping
        """
        if "concurring" in type_raw:
            type_key = CONCURRENCE
        elif "in part" in type_raw:
            type_key = CONCURRING_IN_PART_AND_DISSENTING_IN_PART
        elif "dissenting" in type_raw:
            type_key = DISSENT
        else:
            type_key = MAJORITY

        return types_mapping[type_key]
