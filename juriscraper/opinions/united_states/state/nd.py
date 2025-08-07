# Author: Phil Ardery
# Contact: https://www.ndcourts.gov/contact-us
# History:
# Date created: 2019-02-28
# Updated: 2024-05-08, grossir: to OpinionSiteLinear and new URL
# Updated: 2025-07-02, luism: get citation from HTML

import re
from datetime import date, datetime
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import normalize_dashes
from juriscraper.lib.utils import backscrape_over_paginated_results
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.ndcourts.gov/"
    ordered_fields = [
        "citation",
        "name",
        "docket",
        "date",
        "nature_of_suit",
        "judge",
    ]
    first_opinion_date = datetime(1955, 10, 25)
    # Ensure the backscrape iterable has a single item
    days_interval = (datetime.today() - first_opinion_date).days + 2
    name_regex = re.compile(r"^(.*?)(\s*(\d{4}\sND\s\d+))\s*$")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ndcourts.gov/supreme-court/opinions?topic=&author=&searchQuery=&trialJudge=&pageSize=100&sortOrder=1"
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)
        self.should_have_results = True

    def _process_html(self) -> None:
        """Most values are inside a <p>: whitespace and
        field names need to be cleaned

        Citation used to be available, now must be got from inside
        the document's text
        """
        # Consolidated cases return the same document once per each base docket
        # This may cause the scrape to abort prematurely due to number of
        # consecutive duplicates
        seen_urls = set()

        for row in self.html.xpath('//table//div[@class="row"]'):
            raw_name, *values = list(
                map(str.strip, row.xpath("./div[1]/p[1]/text()"))
            )

            # Do the URL check
            url = urljoin(
                self.base_url,
                row.xpath(".//button[@onclick]/@onclick")[0].split("'")[1],
            )
            if url in seen_urls:
                logger.info(
                    "Skipping %s, we already have a case with url %s",
                    raw_name,
                    url,
                )
                continue
            seen_urls.add(url)

            docket, date, nature, author = [
                txt.split(":", 1)[1].strip() for txt in values if txt
            ]

            if match := self.name_regex.search(raw_name):
                case_name = match.group(1).strip()
                citation = match.group(2).strip()
                raw_name = case_name
            else:
                citation = ""

            case_name, other_docket = self.clean_name(raw_name)

            if other_docket:
                docket = f"{docket}, {other_docket}"

            per_curiam = False
            if "per curiam" in author.lower():
                author = ""
                per_curiam = True

            if summary_texts := row.xpath("./div[2]/p[1]/text()"):
                summary = " ".join(summary_texts).strip()

            self.cases.append(
                {
                    "date": date,
                    "per_curiam": per_curiam,
                    "author": author,
                    "judge": author,
                    "summary": summary,
                    "name": case_name,
                    "citation": citation,
                    "docket": docket,
                    "nature_of_suit": nature,
                    "url": url,
                }
            )

    def clean_name(self, name: str) -> tuple[str, str]:
        """Cleans case name

        Some case names list the consolidated docket or a
        (CONFIDENTIAL) parentheses

        :param name: raw case name
        :return: cleaned name and extra_docket numbers
        """
        other_dockets = ""
        if "(consolidated w/" in name:
            other_dockets = ",".join(re.findall(r"\d{8}", name))
            name = name.split("(consolidated w/")[0]
        if "(CONFIDENTIAL" in name:
            name = name.split("(CONFIDENTIAL")[0]

        return name.strip(), other_dockets

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract model fields from opinion's document text

        The citation is only available in the document's text

        For case_name and docket_number, even if they are available
        in the HTML, the document's text has the best values
        for consolidated cases, where the HTML lists partial
        case names and partial docket numbers

        :param scraped_text: Text of scraped content
        :return: Dict with keys of model's names, and values as dicts
        of models field - value pairs
        """
        metadata = {}
        regex = r"20\d{2}\sND\s\d+"
        citation_match = re.search(regex, scraped_text[:1000])

        if citation_match:
            metadata["Citation"] = citation_match.group(0)

        # Most times, paragraphs are enumerated. The data we are interested
        # in is in a few lines before the first paragraph
        lines = scraped_text.split("\n")
        found = False
        for index, line in enumerate(lines):  # noqa: B007
            if "[¶1]" in line:
                found = True
                break

        if not found:
            return metadata

        case_name, docket_number = "", ""
        reversed_lines = lines[:index][::-1]
        for index, line in enumerate(reversed_lines):
            if re.search(r"\d{8}", line):
                docket_number = line.strip()
                case_name = reversed_lines[index + 1].strip()
                break

        # We only put keys into the objects when they exist
        # Otherwise, we would overwrite existing data with empty values
        metadata.update({"OpinionCluster": {}, "Docket": {}})
        if case_name:
            metadata["Docket"]["case_name"] = case_name
            metadata["OpinionCluster"]["case_name"] = case_name
        if docket_number:
            metadata["Docket"]["docket_number"] = normalize_dashes(
                docket_number
            )

        return metadata

    def _download_backwards(self, dates: tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        start, end = dates
        # last page is 118 (August 2024)
        last_page = 130
        base_url = self.url
        url_template = f"{base_url}&page={{}}"
        self.cases = backscrape_over_paginated_results(
            2, last_page, start, end, "%m/%d/%Y", self, None, url_template
        )
