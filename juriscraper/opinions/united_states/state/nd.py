# Author: Phil Ardery
# Contact: https://www.ndcourts.gov/contact-us
# Date created: 2019-02-28
# Updated: 2024-05-08, grossir: to OpinionSiteLinear and new URL
import re
from datetime import date, datetime
from typing import Tuple
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import normalize_dashes
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.ndcourts.gov/"
    ordered_fields = [
        "name",
        "docket",
        "date",
        "nature_of_suit",
        "judge",
    ]
    first_opinion_date = datetime(1955, 10, 25).date()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ndcourts.gov/supreme-court/opinions?topic=&author=&searchQuery=&trialJudge=&pageSize=100&sortOrder=1"
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

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
            raw_values = list(map(str.strip, row.xpath("./div/p[1]/text()")))
            values = []

            for idx, txt in enumerate(raw_values[:5]):
                if idx == 0:
                    txt, _ = self.clean_name(txt)
                else:
                    txt = txt.split(":", 1)[1].strip()
                values.append(txt)

            summary = (
                " ".join(raw_values[5:]).strip() if len(raw_values) > 5 else ""
            )
            url = urljoin(
                self.base_url,
                row.xpath(".//button[@onclick]/@onclick")[0].split("'")[1],
            )
            if url in seen_urls:
                logger.info(
                    "Skipping %s %s, we already have a case with url %s",
                    raw_values[0],
                    raw_values[1],
                    url,
                )
                continue
            seen_urls.add(url)

            case = dict(zip(self.ordered_fields, values[:5]))
            case.update({"summary": summary, "url": url, "per_curiam": False})

            if "per curiam" in case["judge"].lower():
                case["judge"] = ""
                case["per_curiam"] = True

            self.cases.append(case)

    def clean_name(self, name: str) -> Tuple[str, str]:
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
        regex = r"(?P<volume>20\d{2})\s(?P<reporter>ND)\s(?P<page>\d+)"
        citation_match = re.search(regex, scraped_text[:1000])

        if citation_match:
            # type 8 is a neutral citation in Courtlistener
            metadata["Citation"] = {**citation_match.groupdict(), "type": 8}

        # Most times, paragraphs are enumerated. The data we are interested
        # in is in a few lines before the first paragraph
        lines = scraped_text.split("\n")
        found = False
        for index, line in enumerate(lines):
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

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        start, end = dates
        date_fmt = "%m/%d/%Y"
        # last page is 118 (August 2024)
        first_page, last_page = 2, 130
        base_url = self.url
        cases = []

        for page in range(first_page, last_page):
            self.cases = []  # reset results container
            self.url = f"{base_url}&page={page}"
            self.html = self._download()
            self._process_html()

            # results are ordered by desceding date
            earliest = datetime.strptime(
                self.cases[-1]["date"], date_fmt
            ).date()
            latest = datetime.strptime(self.cases[0]["date"], date_fmt).date()
            logger.info(
                "Results page has date range %s to %s", earliest, latest
            )

            # no intersection between date ranges
            if max(earliest, start) >= min(latest, end):
                # if earliest date from results is earlier than
                # the start date, no need to iterate any further
                if earliest < start:
                    logger.info(
                        "Finishing backscrape: earliest results date is %s earlier than start %s",
                        earliest,
                        start,
                    )
                    break
                continue

            # if there is an intersection, test every case and
            # collect the matching cases
            for case in self.cases:
                case_date = datetime.strptime(case["date"], date_fmt).date()
                if case_date < end and case_date > start:
                    cases.append(case)

        self.cases = cases

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%m/%d/%Y").date()
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y").date()
        else:
            end = datetime.now().date()

        logger.info("Backscraping for cases between %s and %s", start, end)
        self.back_scrape_iterable = [(start, end)]
