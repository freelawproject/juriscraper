"""
Scraper for the Supreme Court of Tennessee
CourtID: tenn
Court Short Name: Tenn.
"""

import re

from juriscraper.lib.type_utils import OpinionType
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
                rows[2].split(": ")[1] if "Authoring Judge" in rows[2] else ""
            )
            lower_court_judge = (
                rows[3].split(": ")[1]
                if "Trial Court Judge" in rows[3]
                else ""
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

    def extract_court_name(self, text: str) -> str:
        """Extract the lower court name from the provided opinion text."""
        # Try regex patterns first
        patterns = [
            r"Appeal by Permission from.+\n(.+)\n",
            r"Appeal from the (.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text[:1000])
            if match:
                return match.group(1).strip()

        # Fallback: find line between case name (with "v.") and case number
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        try:
            case_idx = next(
                i for i, line in enumerate(lines) if re.search(r"\bv\.", line)
            )
            no_idx = next(
                i
                for i in range(case_idx + 1, len(lines))
                if lines[i].startswith("No.")
            )

            # Return the last non-empty line before "No." line
            for i in range(no_idx - 1, case_idx, -1):
                if lines[i]:
                    return lines[i]
        except StopIteration:
            pass

        return ""

    def extract_type(self, type_raw: str) -> str:
        """
        Map a raw opinion type string to a standardized type.

        :param type_raw: Raw type string extracted from the opinion (e.g., 'concurring', 'dissenting')
        :return: Standardized type string from types_mapping
        """
        if "concurring" in type_raw:
            op_type = OpinionType.CONCURRENCE
        elif "in part" in type_raw:
            op_type = OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART
        elif "dissenting" in type_raw:
            op_type = OpinionType.DISSENT
        else:
            op_type = OpinionType.MAJORITY

        return op_type.value
