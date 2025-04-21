"""
Scraper for the Louisiana Second Circuit Court of Appeal
CourtID: lactapp_2
Court Short Name: La. Ct. App. 2d Cir
Author: Gianfranco Huaman
History:
 - 2025-01-11, giancohs: created
"""

import re
from datetime import datetime
from urllib.parse import urlencode, urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.lib.judge_parsers import normalize_judge_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.la2nd.org/opinions/"
        self.year = datetime.now().year
        params = {"opinion_year": self.year}
        self.url = urljoin(self.base_url, f"?{urlencode(params)}")
        self.first_opinion_date = datetime(2019, 7, 17).date()
        self.is_backscrape = False
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        """Process the HTML and extract case information"""
        rows = self.html.xpath('//table[@id="datatable"]/tbody/tr')

        for row in rows:
            author_str = get_row_column_text(row, 4)
            cleaned_author = normalize_judge_string(author_str)[0]
            if cleaned_author.endswith(" J."):
                cleaned_author = cleaned_author[:-3]
            status_str = get_row_column_text(row, 7)
            status = (
                "Published" if "Published" in status_str else "Unpublished"
            )
            date_str = get_row_column_text(row, 1)
            case_date = datetime.strptime(date_str, "%m/%d/%Y").date()

            # Skip if not in date range
            if self.is_backscrape and not self.date_is_in_backscrape_range(
                case_date
            ):
                continue

            self.cases.append(
                {
                    "date": date_str,
                    "docket": get_row_column_text(row, 2),
                    "name": get_row_column_text(row, 3),
                    "author": cleaned_author,
                    "disposition": get_row_column_text(row, 5),
                    "url": get_row_column_links(row, 8),
                    "status": status,
                }
            )

    def make_backscrape_iterable(self, kwargs):
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        Louisiana's opinions page returns all opinions for a year (pagination is not needed),
        so we must filter out opinions not in the date range we are looking for

        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%Y/%m/%d").date()
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%Y/%m/%d").date()
        else:
            end = datetime.now().date()

        self.back_scrape_iterable = [(start, end)]

    def _download_backwards(self, dates):
        """Called when backscraping

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.start_date, self.end_date = dates
        self.is_backscrape = True
        logger.info(
            "Backscraping for range %s %s", self.start_date, self.end_date
        )

        self.year = self.start_date.year
        params = {"opinion_year": self.year}
        self.url = urljoin(self.base_url, f"?{urlencode(params)}")
        self.html = self._download()
        self._process_html()

    def date_is_in_backscrape_range(self, case_date):
        """When backscraping, check if the case date is in
        the backscraping range

        :param date_str: string date from the HTML source
        :return: True if date is in backscrape range
        """
        return self.start_date <= case_date <= self.end_date

    def extract_from_text(self, scraped_text):
        """Extract the following values from the opinion's pdf text. The information we need is in the first page
            - appeal_from_str
            - judges

        :param scraped_text: The text content of the pdf
        :return: Dictionary containing the extracted values that matches the courtlistener model objects
        """
        metadata = {"Docket": {}}

        appeal_from_match = re.search(
            r"Appealed from the\s*(.*?\s*),\s*Louisiana",
            scraped_text,
            re.DOTALL,
        )
        # Judges are in the format "Before [Judge1], [Judge2], and [Judge3], JJ."
        # Sometimes there are more than 3 judges, and other edge cases like "and" is in uppercase
        # or there is no comma between the last two judges
        judges_match = re.findall(
            r"Before\s+(.+?)(?:,\s*|\s+)?(?:and|AND)\s+([A-Z]+),\s+JJ\.",
            scraped_text,
            re.DOTALL,
        )
        if appeal_from_match:
            appeal_from_result = re.sub(
                r"\s+", " ", appeal_from_match.group(1).replace("\n", " ")
            ).strip()
            metadata["Docket"] = {
                "appeal_from_str": appeal_from_result,
            }
        if judges_match:
            initial_judges, last_judge = judges_match[0]
            all_judges = initial_judges.split(",") + [last_judge]
            metadata["OpinionCluster"] = {
                "judges": "; ".join(filter(None, map(str.strip, all_judges))),
            }
        return metadata
