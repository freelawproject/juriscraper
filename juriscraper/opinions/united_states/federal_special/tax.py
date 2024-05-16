# Scraper for the United States Tax Court
# CourtID: tax
# Court Short Name: Tax Ct.
# Neutral Citation Format (Tax Court opinions): 138 T.C. No. 1 (2012)
# Neutral Citation Format (Memorandum opinions): T.C. Memo 2012-1
# Neutral Citation Format (Summary opinions: T.C. Summary Opinion 2012-1
import json
import time
from datetime import date, datetime, timedelta
from typing import Tuple

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(1986, 5, 1)
    days_interval = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_blue_green = None
        self.base = "https://public-api-green.dawson.ustaxcourt.gov/public-api"
        self.url = f"{self.base}/opinion-search"
        self.court_id = self.__module__
        self.td = date.today()
        today = self.td.strftime("%m/%d/%Y")
        self.method = "GET"

        last_month = (self.td - timedelta(days=31)).strftime("%m/%d/%Y")
        self.params = {
            "dateRange": "customDates",
            "startDate": last_month,
            "endDate": today,
            "opinionTypes": "MOP,SOP,TCOP",
        }
        self.make_backscrape_iterable(kwargs)

    def _download(self, request_dict={}):
        """Download from api

        The tax court switches between blue and green deploys so we need to
        check which one is current before we continue

        :param request_dict: An empty dictionary.
        :return: None
        """
        if not self.set_blue_green and not self.test_mode_enabled():
            check = self.request["session"].get(self.url)
            if check.status_code != 200:
                self.base = (
                    "https://public-api-blue.dawson.ustaxcourt.gov/public-api"
                )
                self.url = f"{self.base}/opinion-search"
            self.set_blue_green = True
        if self.test_mode_enabled():
            with open(self.url) as file:
                self.json = json.load(file)
        else:
            self.json = (
                self.request["session"]
                .get(
                    self.url,
                    params=self.params,
                )
                .json()
            )

    def _process_html(self) -> None:
        """Process the html

        Iterate over each item on the page collecting our data.
        return: None
        """
        for case in self.json:
            url = self._get_url(case["docketNumber"], case["docketEntryId"])
            status = (
                "Published"
                if case["documentType"] == "T.C. Opinion"
                else "Unpublished"
            )
            self.cases.append(
                {
                    "judge": case.get(
                        "signedJudgeName", case.get("judge", "")
                    ),
                    "date": case["filingDate"][:10],
                    "docket": case["docketNumber"],
                    "url": url,
                    "name": titlecase(case["caseCaption"]),
                    "status": status,
                }
            )

    def _get_url(self, docket_number: str, docketEntryId: str) -> str:
        """Fetch the PDF URL with AWS API key

        param docket_number: The docket number
        param docketEntryId: The docket entry id
        return: The URL to the PDF
        """
        self.url = f"{self.base}/{docket_number}/{docketEntryId}/public-document-download-url"
        if self.test_mode_enabled():
            # Don't fetch urls when running tests.  Because it requires
            # a second api request.
            return self.url
        pdf_url = super()._download()["url"]
        return pdf_url

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
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = make_date_range_tuples(
            start, end, self.days_interval
        )

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request to the API

        Note that the API returns 100 results or less, so the
        days_interval should be conservative

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.params["startDate"] = dates[0].strftime("%m/%d/%Y")
        self.params["endDate"] = dates[1].strftime("%m/%d/%Y")
        self._download()
        logger.info(
            "Backscraping for range %s %s\n%s cases found",
            *dates,
            len(self.json),
        )
        self._process_html()

        # Using time.sleep to prevent rate limiting
        # {'message': 'you are only allowed 15 requests in a 60 second window time', 'type': 'ip-limiter'}
        if len(self.json) > 0:
            logger.info("Sleeping for 61 seconds to prevent rate limit")
            time.sleep(61)
