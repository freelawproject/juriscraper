from datetime import date, datetime, timedelta

from dateutil import parser
from requests.exceptions import ChunkedEncodingError

from juriscraper.AbstractSite import logger
from juriscraper.DeferringList import DeferringList
from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # Sharin S. Anderson v Alyeska Pipeline Service Co.; Opinion Number: 6496
    first_opinion_date = datetime(2010, 7, 23).date()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_backscrape = False
        self.make_backscrape_iterable(kwargs)
        self.court_id = self.__module__
        self.url = "https://appellate-records.courts.alaska.gov/CMSPublic/Home/Opinions?isCOA=False"
        self.status = "Published"
        # juriscraper in the user agent crashes it
        # it appears to be just straight up blocked.
        self.request["headers"]["user-agent"] = "Free Law Project"
        self.seeds = []
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=30)
        self.dispositions = []

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
                logger.debug("Backscraper skipping %s", adate)
                continue

            for row in table.xpath(".//tr"):
                if row.text_content().strip():
                    try:
                        url = get_row_column_links(row, 1)
                    except IndexError:
                        url = ""

                    # Store case page link for later retrieval
                    self.seeds.append(get_row_column_links(row, 3))
                    self.cases.append(
                        {
                            "date": adate,
                            "docket": get_row_column_text(row, 3),
                            "name": get_row_column_text(row, 4),
                            "citation": get_row_column_text(row, 5),
                            "url": url,
                        }
                    )

    def _get_download_urls(self):
        """Get the download URLs for the cases if missing

        :return: List of download URLs
        """

        def get_download_url(link) -> DeferringList:
            """Retrieve the PDF URL from the alternate page

            :param link: The URL of the case page
            :return The PDF URL or None if not found
            """

            if self.test_mode_enabled():
                # if we're in test mode, return a dummy url and add dummy disposition
                self.dispositions.append("Affirmed")
                return "https://example.com/test.pdf"
            case_html = self._get_html_tree_by_url(link)

            disposition = case_html.xpath("//table[1]//td[3]")[0].text
            self.dispositions.append(disposition)

            download_url = case_html.xpath(
                "//td[contains(@class, 'cms-case-download')]//a/@href"
            )[0]

            if download_url:
                return download_url
            return None

        return DeferringList(seed=self.seeds, fetcher=get_download_url)

    def _get_dispositions(self):
        """Get the dispositions for the cases

        :return: List of dispositions
        """
        return self.dispositions

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
