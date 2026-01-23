"""Scraper for Dept of Justice Office of Legal Counsel
CourtID: bia
Court Short Name: Dept of Justice OLC
Author: William Palin
Reviewer:
Type:
History:
    2022-01-14: Created by William E. Palin
"""

from datetime import date, datetime
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.lib.auth_utils import get_justice_dot_gov_auth_cookies
from juriscraper.lib.exceptions import UnexpectedContentTypeError
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.justice.gov/olc/opinions"
    days_interval = 180
    first_opinion_date = datetime(1934, 3, 16)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.base_url
        self.status = "Published"
        self.url = f"{self.base_url}?items_per_page=40"
        self.make_backscrape_iterable(kwargs)
        self.should_have_results = True

    def _process_html(self):
        for row in self.html.xpath(".//article"):
            name = row.xpath(".//h2")[0].text_content().strip()
            if not name:
                continue
            url = row.xpath(".//a/@href")[0]
            date_filed = row.xpath(".//time")[0].text_content()
            summary = row.xpath(".//p")[0].text_content()
            self.cases.append(
                {
                    "date": date_filed,
                    "name": name,
                    "url": url,
                    "summary": summary,
                    "docket": "",  # Docket numbers don't appear to exist.
                }
            )

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        params = {
            "search_api_fulltext": "",
            "start_date": dates[0].strftime("%m/%d/%Y"),
            "end_date": dates[1].strftime("%m/%d/%Y"),
            "sort_by": "field_date",
            "items_per_page": "40",
        }
        self.url = f"{self.base_url}?{urlencode(params)}"
        self.html = self._download()
        self._process_html()

    def download_content(
        self, download_url, doctor_is_available=True, media_root=""
    ):
        """Overrides regular download_content to handle the
        "I am not a robot challenge". See #1724
        """
        try:
            return super().download_content(
                download_url, doctor_is_available, media_root
            )
        except UnexpectedContentTypeError as exc:
            # access HTML with JS variables to populate cookies
            html_text = exc.data["response"].text
            self.cookies = get_justice_dot_gov_auth_cookies(html_text)
            return super().download_content(
                download_url, doctor_is_available, media_root
            )
