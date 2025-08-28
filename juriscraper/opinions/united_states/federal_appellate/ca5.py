# History:
# - Long ago: Created by mlr
# - 2014-11-07: Updated by mlr to use new website.
# - 2025-08-26: Updated by lmanzur to use OpinionSiteLinear and extract lower court

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.ca5.uscourts.gov/rss.aspx?Feed=Opinions&Which=All&Style=Detail"
        self.court_id = self.__module__

    def _process_html(self):
        for item in self.html.xpath("//item"):
            case_name = item.xpath("description/text()[2]")[0]
            download_url = item.xpath("link")[0].tail
            case_date = item.xpath("description/text()[5]")[0]
            docket_number = item.xpath("description/text()[1]")[0]
            status_raw = item.xpath("description/text()[3]")[0]
            nature_of_suit = item.xpath("description/text()[4]")[0]

            if status_raw == "pub":
                status = "Published"
            elif status_raw == "unpub":
                status = "Unpublished"
            else:
                status = "Unknown"

            # Ensure date is a string, and clean up if needed
            case_date_cleaned = case_date.strip()

            self.cases.append(
                {
                    "name": case_name,
                    "url": download_url,
                    "date": case_date_cleaned,  # Now always a string
                    "docket": docket_number,
                    "status": status,
                    "nature_of_suit": nature_of_suit,
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
               Appeals?\s+from\s+the\s+
             | Petition\s+for\s+Review\s+from\s+an\s+Order\s+of\s+the\s+
             | Petition\s+for\s+Review\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*(?:\.|Nos?\.|USDC))
            """,
            re.X,
        )

        lower_court = ""
        if match := pattern.search(scraped_text):
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
