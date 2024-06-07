"""Scraper for Wyoming Supreme Court
CourtID: wyo
Court Short Name: Wyo.
History:
 - 2014-07-02: mlr: Created new version when court got new website.
 - 2015-07-06: m4h7: Updated to use JSON!
 - 2016-06-09: arderyp: Updated because json endpoint moved and was changed
 - 2024-04-12: grossir: update to OpinionSiteLinear and implement dynamic backscraper
"""

import re
from datetime import date, datetime
from typing import Optional, Tuple
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    date_re = re.compile(r"^/Date\((\d+)\)/$")
    base_url = "http://www.courts.state.wy.us"
    api_url = "https://opinions.courts.state.wy.us/Home/GetOpinions"
    document_url = "https://documents.courts.state.wy.us/Opinions"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.set_url(datetime(datetime.today().year, 1, 1))
        self.make_backscrape_iterable(kwargs)
        self.status = "Published"

    def _process_html(self) -> None:
        """Process HTML into case dictionaries

        :return: None
        """
        self.json = self.html

        for opinion in self.json:
            pdf_file_name = opinion["DocumentName"]
            if pdf_file_name[:5] == "../..":
                pdf_file_name = pdf_file_name[5:]
            url = f"{self.document_url}/{pdf_file_name}".replace(" ", "%20")

            match = self.date_re.match(opinion["date_heard"])
            timestamp = int(match.group(1)) / 1000
            date_filed = datetime.fromtimestamp(timestamp).strftime("%m/%d/%Y")

            self.cases.append(
                {
                    "name": f"{opinion['Appellant']} v. {opinion['Appellee']}",
                    "url": url,
                    "date": date_filed,
                    "docket": opinion["DocketNumber"],
                    "citation": opinion["OpinionID"],
                }
            )

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Sets self.url

        If neither StartDate or EndDate query string parameters
        are passed, the API returns all the dataset

        :param start: start date
        :param end: end date

        :return: None
        """
        params = {}

        if start:
            params["StartDate"] = start.strftime("%m/%d/%Y")
        if end:
            params["EndDate"] = end.strftime("%m/%d/%Y")

        if params:
            self.url = f"{self.api_url}?{urlencode(params)}"
        else:
            self.url = self.api_url

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = self._download()
        self._process_html()

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
            start = None
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = [(start, end)]
