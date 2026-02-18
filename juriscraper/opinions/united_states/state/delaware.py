"""Scraper for the Supreme Court of Delaware
CourtID: del

Creator: Andrei Chelaru
Reviewer: mlr
"""

import re
from urllib.parse import urljoin

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "https://courts.delaware.gov/opinions/List.aspx?ag=supreme%20court"
        )
        # Note that we can't do the usual thing here because 'del' is a Python keyword.
        self.court_id = "juriscraper.opinions.united_states.state.del"
        self.should_have_results = True
        self.status = "Published"

    def _process_html(self):
        """Process the html and extract out the opinions

        :return: None
        """
        for row in self.html.xpath("//table//tr[not(th)]"):
            case = {
                "name": row.xpath("td[1]/a/text()")[0].strip(),
                "date": row.xpath("td[2]/span/text()")[0].strip(),
                "docket": row.xpath("td[3]/span/text()")[0].strip(),
                "url": urljoin(
                    self.url, row.xpath("td[1]/a/@href")[0].strip()
                ),
                "judge": " ".join(row.xpath("td[6]/text()")).strip(),
                "per_curiam": False,
            }
            if "per curiam" in case["judge"].lower():
                case["judge"] = ""
                case["per_curiam"] = True

            self.cases.append(case)

    def extract_from_text(self, scraped_text: str) -> dict:
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

        result = {}

        if match := pattern.search(cleaned_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            result["Docket"] = {"appeal_from_str": lower_court}

            if number_match := number_pattern.search(cleaned_text):
                lower_court_number = number_match.group(
                    "lower_court_number"
                ).strip()
                result["OriginatingCourtInformation"] = {
                    "docket_number": lower_court_number
                }

        return result
