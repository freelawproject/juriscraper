"""Scraper for the D.C. Court of Appeals
CourtID: dc
Court Short Name: D.C.
Author: V. David Zvenyach
Date created:2014-02-21
History:
    - 2025-08-29: Update to OpinionSiteLinear and added extract_from_text method to get lower court info, Luis Manzur
"""

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.dccourts.gov/court-of-appeals/opinions-memorandum-of-judgments"
        qualifier_no_opinions = (
            'not(contains(td[2]/span/text(), "NO OPINIONS"))'
        )
        qualifier_has_pdf_link = 'contains(.//td[1]/a/@href, ".pdf")'
        self.base_path = f"//table//tr[{qualifier_no_opinions} and {qualifier_has_pdf_link}]"
        self.should_have_results = True
        self.status = "Published"

    def _process_html(self):
        """Process the html and extract out the opinions

        :return: None
        """

        for row in self.html.xpath(self.base_path):
            docket = row.xpath("./td[1]/a/text()")[0].strip()
            url = row.xpath("./td[1]/a/@href")[0].strip()
            name = row.xpath("./td[2]/text()")[0].strip()
            date = row.xpath("./td[3]/text()")[0].strip()
            self.cases.append(
                {
                    "name": name,
                    "date": date,
                    "docket": docket,
                    "url": url,
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """

        court_and_docket_pattern = re.compile(
            r"""
            (?:
               Appeals?\s+from\s+the\s+
               | On\s+Report\s+and\s+Recommendation\s+of\s+the\s+
               | On\s+Petition\s+for\s+Review\s+of\s+a\s+Decision(?:\s*\n*\s*|\s+)of\s+the\s+
               | On\s+Certified\s+Question\s+from\s+the\s+
               | On\s+Petition\s+for\s+Review\s+of\s+an\s+Order\s+of\s+the\s+
            )
            (.*?)
            \s*\n*\s*\(([^)]+)\)
            """,
            re.X | re.DOTALL | re.MULTILINE | re.IGNORECASE,
        )

        match = court_and_docket_pattern.search(scraped_text)
        if match:
            lower_court = re.sub(r"\s+", " ", match.group(1)).strip()
            lower_court_number = match.group(2).strip()

            return {
                "Docket": {
                    "appeal_from_str": lower_court,
                },
                "OriginatingCourtInformation": {
                    "docket_number": lower_court_number,
                },
            }

        return {}
