"""
CourtID: cadc
Court Short Name: Court of Appeals of the District of Columbia
Author: mlissner
History:
    2014-07-31, mlissner: commited first version
    2024-12-31, grossir: Implemented new site
    2025-08-26, lmanzur: Updated added extract_from_text.
"""

import re

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # https://media.cadc.uscourts.gov/opinions/
        self.url = "https://media.cadc.uscourts.gov/opinions/bydate/recent"
        self.status = "Published"

    def _process_html(self):
        link_xpath = "a[contains(@href, '.pdf')]"
        for row in self.html.xpath(f"//div[div[div[div[{link_xpath}]]]]"):
            self.cases.append(
                {
                    "url": row.xpath(f".//{link_xpath}/@href")[0],
                    "docket": row.xpath(f".//{link_xpath}/text()")[0],
                    "name": row.xpath("div[2]/div/div/text()")[0],
                    "date": row.xpath(".//span/text()")[-1],
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """

        pattern = re.compile(
            r"""
            (?:
               (?:On\s+)?Appeals?\s+from\s+the\s+
              | (?:On\s+)?Petitions?\s+for\s+Review\s+of\s+(?:a\s+)?(?:Final\s+)?Action\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*(?:\.|\(|Nos?\.|USC|D.C.|\n\s*\n))
            """,
            re.X | re.IGNORECASE,
        )

        lower_court = ""
        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()

        if lower_court:
            return {
                "Docket": {
                    "appeal_from_str": titlecase(lower_court),
                }
            }

        return {}
