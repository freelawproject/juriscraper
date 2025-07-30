# Scraper for Texas Business Court
# CourtID: texb
# Court Short Name: TX
# Court Contacts:
#  - http://www.txcourts.gov/contact-us/
#  - Blake Hawthorne <Blake.Hawthorne@txcourts.gov>
#  - Eddie Murillo <Eddie.Murillo@txcourts.gov>
#  - Judicial Info <JudInfo@txcourts.gov>
# Author: Luis Manzur
# History:
#  - 2025-07-29: Created by Luis Manzur
import re

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    pattern = r"^(\S+)\s+(.+?)(?:\s+(\d{4} Tex\. Bus\. \d+))?$"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.txcourts.gov/businesscourt/opinions/"
        self.court_id = self.__module__
        self.status = "Published"
        self.should_have_results = True

    def _process_html(self) -> None:
        """Parses the HTML content

        :return None
        """

        links = self.html.xpath('//div[@class="panel-content"]//a')

        for link in links:
            opinion_date_str = link.xpath("./preceding::h2[1]")[0].text.strip()

            text = link.text
            if not text:
                continue

            match = re.match(self.pattern, text)

            if match:
                self.cases.append(
                    {
                        "docket": match.group(1),
                        "name": titlecase(match.group(2)),
                        "citation": match.group(3) or "",
                        "url": link.get("href"),
                        "date": opinion_date_str,
                    }
                )
