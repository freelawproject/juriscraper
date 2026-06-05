# Scraper for Texas Business Court
# CourtID: texbizct
# Author: Luis Manzur
# History:
#  - 2025-07-29: Created by Luis Manzur
#  - 2026-06-05: Parse judge and date from the byline; the source now
#    publishes them. #1992
import re
from urllib.parse import urljoin

from dateutil import parser

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

logger = make_default_logger()

# e.g. "Whitehill, J. | June 3, 2026"; the source has typos like
# "Stagner, J," and "January 26. 2026", so be lenient about punctuation
byline_regex = re.compile(
    r"(?P<judge>.*?)[,.]?\s*J[.,]?\s*\|\s*(?P<date>[A-Za-z]+ \d{1,2}[.,]? \d{4})"
)


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.txcourts.gov/businesscourt/opinions/"
        self.court_id = self.__module__
        self.should_have_results = True
        self.status = "Published"

    async def _process_html(self) -> None:
        """Parses the HTML content

        :return None
        """

        # The example saved in 2025 had the whole panel repeated 7 times;
        # track seen URLs in case the source ever duplicates content again
        seen_urls = set()
        links = self.html.xpath('//div[@class="panel-content"]//h2/a')
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

            url = urljoin(self.url, link.get("href"))
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # A byline paragraph follows each opinion's h2 heading, e.g.
            # "Whitehill, J. | June 3, 2026" #1992
            judge, case_date = "", ""
            date_filed_is_approximate = False
            byline = link.xpath("../following-sibling::*[1][self::p]")
            byline_text = byline[0].text_content().strip() if byline else ""
            if match := byline_regex.search(byline_text):
                judge = match.group("judge")
                case_date = match.group("date")
            else:
                # `extract_from_text` will get the exact date from the
                # document
                logger.warning(
                    "texbizct: no judge/date byline for %s; got %r",
                    url,
                    byline_text,
                )
                # Use a mid-year date on the citation's year; if there is
                # no citation either, dateutil defaults to the current year
                year_match = re.search(r"\d{4}", citation)
                year = year_match.group(0) if year_match else ""
                case_date = f"July 1, {year}".strip(" ,")
                date_filed_is_approximate = True

            raw_docket = title.split()[0]
            docket = raw_docket.strip(",").replace("--", "-")

            summary = link.xpath("../following-sibling::ul[1]/li/text()")
            summary = " ".join(summary)

            self.cases.append(
                {
                    "docket": docket,
                    "name": name.split("(", 1)[0].strip(),
                    "citation": citation.split("(", 1)[0].strip(),
                    "url": url,
                    "date": case_date,
                    "date_filed_is_approximate": date_filed_is_approximate,
                    "judge": judge,
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
