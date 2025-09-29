# Scraper for California's First District Court of Appeal
# CourtID: calctapp_1st
# Court Short Name: Cal. Ct. App.

import re

from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    court_code = "A"
    division = "1st App. Dist."

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """

        pattern = re.compile(
            r"""
            (?:
            Trial\s+Court:\s+|
             (?:APPEALS?|Appeals?)\s+from\s+a\s+(?:judgments?|postjudgments?)(?:\s+order)?\s+of\s+the\s+|
             (?:APPEALS?|Appeals?)\s+from\s+(?:an\s+)?orders?\s+of\s+the\s+|
             (?:APPEALS?|Appeals?)\s+from\s+the\s+
             )
            (?P<lower_court>[A-Za-z\s]*?)(?=,|\n\s*\n|\.|Nos?.)
            """,
            re.X | re.DOTALL,
        )

        fall_back_pattern = re.compile(
            r"(?P<lower_court>[A-Za-z\s]+County\s+Super\. Ct\.)", re.MULTILINE
        )

        lower_court = ""
        if (match := pattern.search(scraped_text)) or (
            match := fall_back_pattern.search(scraped_text)
        ):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

        if lower_court:
            return {
                "Docket": {
                    "appeal_from_str": lower_court,
                }
            }
        return {}
