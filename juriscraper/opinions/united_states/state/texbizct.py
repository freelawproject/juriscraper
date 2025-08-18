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

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

logger = make_default_logger()


class Site(OpinionSiteLinear):
    case_info_pattern = r"^(\S+)\s+(.+?)(?:\s+(\d{4} Tex\. Bus\. \d+))?(?:\s+(?:Opinion|Memorandum|Denied|Some Defendants Dismissed|Remand|Reconsideration|Me|MSJ|PTJ|Rule).*)?$"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.txcourts.gov/businesscourt/opinions/"
        self.court_id = self.__module__
        self.status = "Unknown"
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
                logger.debug("Skipping link with empty text: %s", link)
                continue

            match = re.match(self.case_info_pattern, text)

            if match:
                self.cases.append(
                    {
                        "docket": match.group(1),
                        "name": titlecase(match.group(2).strip()),
                        "citation": match.group(3) or "",
                        "url": link.get("href"),
                        "date": opinion_date_str,
                    }
                )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extracts case citation from the scraped text.

        :param scraped_text: The text content of the opinion.
        :return: A dictionary with case details.
        """
        pattern = r"(\d{4})\sTex\.\sBus\.\s(?:Ct\.\s)?(\d+)"
        match = re.search(pattern, scraped_text)
        status = "Published" if match else "Unknown"
        citation = match.group(0) if match else ""
        return {
            "Citation": citation,
            "OpinionCluster": {
                "precedential_status": status,
            },
        }
