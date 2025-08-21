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
from datetime import datetime

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
            short_title = link.text_content()
            if not text:
                logger.debug("Skipping link with empty text: %s", link)
                continue

            summary = ""
            summary_list = link.xpath("following::li[1]/text()")
            if summary_list:
                summary = summary_list[0].strip()

            match = re.match(self.case_info_pattern, text)

            split_short_title = short_title.split(",")
            name = (
                titlecase(match.group(2).strip())
                if match
                else split_short_title[0].strip()
            )
            citation = (
                split_short_title[-1].strip()
                if short_title
                else (match.group(3) or "")
            )

            case = {
                "docket": match.group(1) if match else "temp-docket",
                "name": name,
                "citation": citation,
                "url": link.get("href"),
                "date": f"{citation[:4]}/07/01",
                "date_filed_is_approximate": True,
                "status": "Published" if citation else "Unknown",
                "summary": summary,
            }

            self.cases.append(case)

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extracts date filled  from the scraped text.

        :param scraped_text: The text content of the opinion.
        :return: A dictionary with case details.
        """

        date_filed_pattern = r"(?:\:|Signed)\s*([A-Za-z]+\s\d{1,2},\s\d{4})"
        date_filed_match = re.search(date_filed_pattern, scraped_text)
        date_filed = (
            date_filed_match.group(1).strip() if date_filed_match else ""
        )

        # Docket number pattern: 24-BC04A-0002
        docket_pattern = r"\b\d{2}-BC\d{2}[A-Z]-\d{4}\b"
        docket_match = re.search(docket_pattern, scraped_text)
        docket_number = docket_match.group(0) if docket_match else None

        # Convert to ISO format if found
        date_filed_iso = ""
        if date_filed:
            try:
                date_obj = datetime.strptime(date_filed, "%B %d, %Y")
                date_filed_iso = date_obj.date().isoformat()
            except ValueError:
                logger.error(
                    "Failed to parse date '%s' from text: %s",
                    date_filed,
                )
                date_filed_iso = None  # fallback to empty if parsing fails

        result = {}
        if date_filed_iso or docket_number:
            result.setdefault("OpinionCluster", {})
        if date_filed_iso:
            result["OpinionCluster"]["date_filed"] = date_filed_iso
            result["OpinionCluster"]["date_filed_is_approximate"] = False
        if docket_number:
            result["OpinionCluster"]["docket_number"] = docket_number
        return result
