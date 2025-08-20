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
        self.should_have_results = True

    def _process_html(self) -> None:
        """Parses the HTML content

        :return None
        """

        links = self.html.xpath('//div[@class="panel-content"]//a')
        for link in links:
            text = link.get("title")
            short_title = link.text
            if not text:
                logger.debug("Skipping link with empty text: %s", link)
                continue

            summary = ""
            summary_list = link.xpath("following::li[1]/text()")
            if summary_list:
                summary = summary_list[0].strip()

            match = re.match(self.case_info_pattern, text)
            if match:
                citation = (
                    short_title.split(",")[-1].strip()
                    if short_title
                    else (match.group(3) or "")
                )

                self.cases.append(
                    {
                        "docket": match.group(1),
                        "name": titlecase(match.group(2).strip()),
                        "citation": citation,
                        "url": link.get("href"),
                        "date": f"{citation[:4]}/07/01",
                        "date_filed_is_approximate": True,
                        "status": bool(citation),
                        "summary": summary,
                    }
                )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extracts date filled  from the scraped text.

        :param scraped_text: The text content of the opinion.
        :return: A dictionary with case details.
        """

        date_filled_pattern = r"(?:\:|Signed)\s*([A-Za-z]+\s\d{1,2},\s\d{4})"
        date_filled_match = re.search(date_filled_pattern, scraped_text)
        date_filled = (
            date_filled_match.group(1).strip() if date_filled_match else ""
        )

        # Convert to ISO format if found
        date_filled_iso = ""
        if date_filled:
            try:
                from datetime import datetime

                date_obj = datetime.strptime(date_filled, "%B %d, %Y")
                date_filled_iso = date_obj.date().isoformat()
            except Exception:
                date_filled_iso = ""  # fallback to empty if parsing fails

        if not date_filled_iso:
            return {}
        return {
            "OpinionCluster": {
                "date_filled": date_filled_iso,
                "date_filed_is_approximate": False,
            },
        }
