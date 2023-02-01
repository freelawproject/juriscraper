"""
Scraper for Virginia Attorney General
CourtID: vaag
Court Short Name: VA AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import re
from datetime import datetime as dt

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.oag.state.va.us/citizen-resources/opinions/official-opinions"
        self.year = dt.today().year

    def _process_html(self):
        """Process html

        :return: None
        """
        if not self.test_mode_enabled():
            self.url = self.html.xpath(
                f".//a[contains(@href, '{self.year}-official-opinions')]/@href"
            )[0]
            self.html = super()._download()
        else:
            # Assign date for testing purposes, which is collected via extract
            # from text later
            self.year = "2023-01-31"
        for row in self.html.xpath(
            ".//tr/td/strong/a[contains(@href, '.pdf')]/../../.."
        ):
            cells = row.xpath(".//td")
            url = row.xpath(".//@href")[0]
            docket = row.xpath(".//a/text()")[0]
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": f"Opinion {docket}",
                    "summary": cells[2].text_content(),
                    "date": str(self.year),
                    "date_filed_is_approximate": True,
                }
            )

    def extract_from_text(self, scraped_text):
        """Extact date from pdf

        :param scraped_text:
        :return:
        """
        pattern = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")
        match = pattern.search(scraped_text)
        if match:
            date_filed = dt.strptime(match.group(), "%B %d, %Y").strftime(
                "%Y-%m-%d"
            )
            metadata = {
                "OpinionCluster": {
                    "date_filed": date_filed,
                    "date_filed_is_approximate": False,
                },
            }
            return metadata
