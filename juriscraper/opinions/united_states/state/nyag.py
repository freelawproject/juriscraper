"""Scraper for the New York Attorney General
CourtID: nyag
Court Short Name: New York Attorney General
"""

import re
from datetime import datetime

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://ag.ny.gov/libraries-documents/opinions/opinions-year"
        )

        self.parameters = {
            "name": "",
            "field_opinion_number_value": "",
            "field_opinion_type_target_id": "All",
            "sort_bef_combine": "field_opinion_date_value_DESC",
        }

    def _process_html(self):
        for row in self.html.xpath("//div[@class='views-row']"):
            docket_div, formal_div, _, summary_div, *_ = row.xpath(
                ".//div[contains(@class, 'field-content')]"
            )
            docket = docket_div.text_content()
            summary = summary_div.text_content()
            url = row.xpath(".//div/span/p/a")[0].get("href")
            case = row.xpath(".//div/span/p/a/text()")[0]
            if not formal_div.text_content():
                logger.warning(
                    f"{self.court_id}: Skipping row with no status."
                )
                continue
            status = (
                "Published"
                if formal_div.text_content() == "Formal"
                else "Unpublished"
            )
            self.cases.append(
                {
                    "name": case,
                    "docket": docket,
                    "url": url,
                    "summary": summary,
                    "date": f"{docket[:4]}-07-01",
                    "date_filed_is_approximate": True,
                    "status": status,
                }
            )

    def extract_from_text(self, scraped_text) -> dict:
        """Extract date from text

        :param scraped_text:
        :return: Metadata if any
        """
        date_pattern = r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b"

        # Find all dates
        dates = re.findall(date_pattern, scraped_text)
        if not dates:
            return {}
        date_filed = datetime.strptime(dates[0], "%B %d, %Y").strftime(
            "%Y-%m-%d"
        )

        metadata = {
            "OpinionCluster": {
                "date_filed": date_filed,
                "date_filed_is_approximate": False,
            },
        }
        return metadata
