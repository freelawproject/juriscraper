"""
Scraper for Nevada Attorney General
CourtID: nevag
Court Short Name: Nevada AG
Author: William E. Palin
History:
 - 2023-01-29: Created.--- could probably use a text extract for the date, but
  would you believe that the pdfs are images.
"""
import datetime
import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://ag.nv.gov/Publications/Opinions/"

    def _process_html(self):
        """Process html

        :return: None
        """
        for row in self.html.xpath(".//a"):
            if "AGO-" not in row.text_content():
                continue
            name = row.text_content()
            docket = name
            url = row.xpath(".//@href")[0]
            if self.test_mode_enabled():
                date = "2023-01-31"
            else:
                date = (name.split("-")[1],)
            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": name,
                    "date": date,
                    "date_filed_is_approximate": True,
                }
            )

    def extract_from_text(self, scraped_text):
        """Extract date metadata from PDF

        :param scraped_text: Scraped content
        :return: Metadata containing date info
        """
        pattern = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")
        match = pattern.search(scraped_text)
        if match:
            date_filed = datetime.datetime.strptime(
                match.group(), "%B %d, %Y"
            ).strftime("%Y-%m-%d")
            metadata = {
                "OpinionCluster": {
                    "date_filed": date_filed,
                    "date_filed_is_approximate": False,
                },
            }
            return metadata
