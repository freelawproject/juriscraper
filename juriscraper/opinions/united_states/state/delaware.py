"""Scraper for the Supreme Court of Delaware
CourtID: del

Creator: Andrei Chelaru
Reviewer: mlr
"""

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "http://courts.delaware.gov/opinions/list.aspx?ag=supreme%20court"
        )
        # Note that we can't do the usual thing here because 'del' is a Python keyword.
        self.court_id = "juriscraper.opinions.united_states.state.del"
        self.should_have_results = True
        self.status = "Published"

    def _process_html(self):
        """Process the html and extract out the opinions

        :return: None
        """
        for row in self.html.xpath("//table/tr"):
            self.cases.append(
                {
                    "name": row.xpath("./td[1]/a/text()")[0].strip(),
                    "date": row.xpath("./td[2]/text()")[0].strip(),
                    "docket": row.xpath("./td[3]/a/text()")[0].strip(),
                    "url": row.xpath("./td[1]/a/@href")[0].strip(),
                    "judge": " ".join(row.xpath("./td[6]/text()")),
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """

        pattern = re.compile(
            r"""
            §?\s*Court\s+Below[\u2013\u2014\-:]
            (?P<lower_court>.*?)(?=\s{2,}|§|v\.)
            """,
            re.X | re.IGNORECASE,
        )

        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            return {
                "Docket": {
                    "appeal_from_str": f"{lower_court} of the State of Delaware",
                }
            }

        return {}
