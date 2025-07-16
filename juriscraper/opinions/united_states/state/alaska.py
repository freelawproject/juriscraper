from datetime import date, datetime, timedelta
from urllib.parse import urlencode, urljoin

from dateutil import parser
from requests.exceptions import ChunkedEncodingError

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import (
    get_row_column_text,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # Sharin S. Anderson v Alyeska Pipeline Service Co.; Opinion Number: 6496
    first_opinion_date = datetime(2010, 7, 23).date()
    base_url = "https://appellate-records.courts.alaska.gov/CMSPublic/"
    # endpoint for opinion url without parameters
    op_endpoint = urljoin(base_url, "UserControl/OpenOpinionDocument")
    is_coa = False
    search_parameter = "Opinions"
    document_type = "OP"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_backscrape = False
        self.make_backscrape_iterable(kwargs)
        self.court_id = self.__module__
        self.url = urljoin(
            self.base_url, f"Home/{self.search_parameter}?isCOA={self.is_coa}"
        )
        self.status = "Published"
        # juriscraper in the user agent crashes it
        # it appears to be just straight up blocked.
        self.request["headers"]["user-agent"] = "Free Law Project"
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=30)
        self.is_citation_visible = True

    def _download(self, request_dict=None):
        # Unfortunately, about 2/3 of calls are rejected by alaska but
        # if we just ignore those encoding errors we can live with it
        if request_dict is None:
            request_dict = {}
        try:
            return super()._download(request_dict)
        except ChunkedEncodingError:
            return None

    def _process_html(self) -> None:
        if not self.html:
            logger.info(
                "HTML was not downloaded from source page. Should retry"
            )
            return
        for table in self.html.xpath("//table"):
            adate = table.xpath("./preceding-sibling::h5")[0].text_content()
            if (
                not self.date_is_in_range(adate)
                and not self.test_mode_enabled()
            ):
                if self.is_backscrape:
                    logger.debug("Backscraper skipping %s", adate)
                    continue
                break

            for row in table.xpath(".//tr"):
                if row.text_content().strip():
                    case_number = get_row_column_text(row, 3)
                    name = get_row_column_text(row, 4)
                    citation = (
                        get_row_column_text(row, 5)
                        if self.is_citation_visible
                        else ""
                    )

                    # get parameters required to build opinion url
                    params = {
                        "docNumber": get_row_column_text(row, 2),
                        "caseNumber": case_number.split(",")[0],
                        "opinionType": self.document_type,
                    }
                    url = f"{self.op_endpoint}?{urlencode(params)}"

                    self.cases.append(
                        {
                            "date": adate,
                            "docket": case_number,
                            "name": name,
                            "citation": citation,
                            "url": url,
                        }
                    )

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        Alaska's opinions page returns all opinions, so we must only load it
        (successfully, because it may load partially) once.
        We can use the backscrape arguments to filter out opinions not in the
        date range we are looking for

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

        self.back_scrape_iterable = [(start, end)]

    def _download_backwards(self, dates: tuple[date]) -> None:
        """Called when backscraping

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.start_date, self.end_date = dates
        self.is_backscrape = True
        logger.info(
            "Backscraping for range %s %s", self.start_date, self.end_date
        )

    def date_is_in_range(self, date_str: str) -> bool:
        """Check if the table date is in
        the range

        :param date_str: string date from the HTML source
        :return: True if date is in backscrape range
        """
        parsed_date = parser.parse(date_str).date()
        return self.start_date <= parsed_date <= self.end_date
