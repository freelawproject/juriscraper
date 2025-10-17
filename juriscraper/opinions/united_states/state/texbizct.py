# Scraper for Texas Business Court
# CourtID: texbizct
# Author: Luis Manzur
# History:
#  - 2025-07-29: Created by Luis Manzur
import re
from typing import Optional

from dateutil import parser

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

logger = make_default_logger()


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.txcourts.gov/businesscourt/opinions/"
        self.court_id = self.__module__
        self.should_have_results = True
        self.status = "Published"

    def _process_html(self) -> None:
        """Parses the HTML content

        :return None
        """

        links = self.html.xpath('//div[@class="panel-content"]//a')
        for link in links:
            title = link.get("title")
            short_title = link.text_content()

            # Attempt to split the short_title by the last comma to extract name and citation.
            # If that fails, try splitting the title instead.
            # If both attempts fail, assign the entire title to name and leave citation empty.
            try:
                name, citation = short_title.rsplit(", ", 1)
            except (ValueError, AttributeError):
                try:
                    citation = title.rsplit(", ", 1)[-1]
                    name = short_title
                except (ValueError, AttributeError):
                    name, citation = short_title, ""

            url = link.get("href")
            date = self._get_approximate_date(url)
            raw_docket = title.split()[0]
            docket = raw_docket.strip(",").replace("--", "-")

            summary = link.xpath("../following-sibling::ul/li/text()")
            summary = " ".join(summary)

            self.cases.append(
                {
                    "docket": docket,
                    "name": name.split("(", 1)[0].strip(),
                    "citation": citation.split("(", 1)[0].strip(),
                    "url": url,
                    "date": date,
                    "date_filed_is_approximate": True,
                    "summary": summary,
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extracts date filed from the scraped text.

        :param scraped_text: The text content of the opinion.
        :return: A dictionary with case details.
        """

        # Get date from stamp on first page
        pattern = r"\b(\d{1,2}/\d{1,2}/\d{4})\b"
        dates = re.findall(pattern, scraped_text[:500])
        if dates:
            date_filed = dates[0]
        else:
            # if no stamp grab from signature block
            date_filed_pattern = (
                r"(?:\:|Signed)\s*([A-Za-z]+\s\d{1,2},\s\d{4})"
            )
            date_filed_match = re.search(date_filed_pattern, scraped_text)
            date_filed = (
                date_filed_match.group(1) if date_filed_match else None
            )

        if date_filed:
            dt = parser.parse(date_filed)
            date_string = dt.strftime("%Y-%m-%d")
            return {
                "OpinionCluster": {
                    "date_filed": date_string,
                    "date_filed_is_approximate": False,
                }
            }
        return {}

    def _get_approximate_date(self, url: str) -> Optional[str]:
        """Get Approximate date from head request

        :param url: The pdf url
        :return: The date the file was last touched
        """
        if self.test_mode_enabled():
            return "2025-01-01"
        resp = self.request["session"].head(
            url, allow_redirects=True, timeout=30
        )
        lm = resp.headers.get("Last-Modified")
        dt = parser.parse(lm)
        return dt.strftime("%Y-%m-%d")
