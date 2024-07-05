# Scraper for New York Appellate Term 1st Dept.
# CourtID: nyappterm_1st
# Court Short Name: NY

import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = date(2003, 9, 25)

    # If more than 500 results are found, no results will be shown
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court = "Appellate Term, 1st Dept"
        self.court_id = self.__module__
        self.url = "https://iapps.courts.state.ny.us/lawReporting/Search?searchType=opinion"
        self._set_parameters()
        self.expected_content_types = ["application/pdf", "text/html"]
        self.make_backscrape_iterable(kwargs)

    def _set_parameters(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> None:
        """Set the parameters for the POST request.

        If no start or end dates are given, scrape last month.
        This is the default behaviour for the present time scraper

        :param start_date:
        :param end_date:

        :return: None
        """
        self.method = "POST"

        if not end_date:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

        self.parameters = {
            "rbOpinionMotion": "opinion",
            "Pty": "",
            "and_or": "and",
            "dtStartDate": start_date.strftime("%m/%d/%Y"),
            "dtEndDate": end_date.strftime("%m/%d/%Y"),
            "court": self.court,
            "docket": "",
            "judge": "",
            "slipYear": "",
            "slipNo": "",
            "OffVol": "",
            "Rptr": "",
            "OffPage": "",
            "fullText": "",
            "and_or2": "and",
            "Order_By": "Party Name",
            "Submit": "Find",
            "hidden1": "",
            "hidden2": "",
        }

    def _process_html(self):
        for row in self.html.xpath(".//table")[-1].xpath(".//tr")[1:]:
            slip_cite = " ".join(row.xpath("./td[5]//text()"))
            official_citation = " ".join(row.xpath("./td[4]//text()"))
            url = row.xpath(".//a")[0].get("href")
            url = re.findall(r"(http.*htm)", url)[0]
            status = "Unpublished" if "(U)" in slip_cite else "Published"
            self.cases.append(
                {
                    "name": row.xpath(".//td")[0].text_content(),
                    "date": row.xpath(".//td")[1].text_content(),
                    "url": url,
                    "status": status,
                    "docket": "",
                    "citation": official_citation,
                    "parallel_citation": slip_cite,
                }
            )

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the date filed from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        # Ny App Term 1st Dept. 2nd and Sup Ct all have different varying
        # docket number types.
        # ie. 123413/03 vs. 51706 vs. 2003-718 Q C or 2003-1288 K C

        dockets = re.findall(
            r"(\d+\/\d+)|^(\d{5,})|^(\d+-\d+ \w+\s\w+)", scraped_text
        )
        dockets = [list(filter(None, x)) for x in dockets]
        metadata = {
            "Docket": {
                "docket_number": dockets[0][0] if dockets else "",
            },
        }
        return metadata

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Make custom date range request

        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self._set_parameters(*dates)
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
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = make_date_range_tuples(
            start, end, self.days_interval
        )
