"""
Scraper for Kansas Supreme Court - Published
CourtID: kan_p
Court Short Name: Kansas
Author: William Palin
Court Contact:
History:
 - 2025-06-09: Created.
 - 2026-03-19: Refactored from WebDriven to OpinionSiteLinear. grossir
    Use urllib to fix block
    Added backscraper
 - 2026-04-02: Split into kan_p and kan_u by status. grossir
"""

from datetime import date, timedelta
from urllib.parse import urlencode, urljoin

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://searchdro.kscourts.gov"
    court_string = "Supreme Court"
    court_filter = "10"
    status_filter = "1"
    status = "Published"
    first_opinion_date = date(2015, 1, 1)
    days_interval = 30
    use_urllib = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = self._make_search_url(today - timedelta(days=30), today)
        self.make_backscrape_iterable(kwargs)

    def _make_search_url(self, start: date, end: date) -> str:
        params = {
            "StartDate": start.strftime("%Y-%m-%d"),
            "EndDate": end.strftime("%Y-%m-%d"),
            "statusFilter": self.status_filter,
            "courtFilter": self.court_filter,
            "Keyword": "",
        }
        return urljoin(self.base_url, f"/Documents/Search?{urlencode(params)}")

    def _process_html(self) -> None:
        """Parse the /Documents/Search results table.

        Columns: Release Date, Case Number, Case Title, Court, Status, PDF
        """

        for row in self.html.xpath("//table//tr[not(.//th)]"):
            cells = row.xpath(".//td")
            if len(cells) < 6:
                logger.warning("Skipping malformed row %s", cells)
                continue

            court = cells[3].text_content().strip()
            if court != self.court_string:
                logger.warning("Skipping record from other court, %s", cells)
                continue

            url = cells[5].xpath(".//a/@href")
            self.cases.append(
                {
                    "date": cells[0].text_content().strip(),
                    "docket": cells[1].text_content().strip(),
                    "name": cells[2].text_content().strip(),
                    "status": cells[4].text_content().strip(),
                    "url": urljoin(self.base_url, url[0]),
                }
            )

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Backscrape using the /Documents/Search endpoint

        :param dates: (start_date, end_date) tuple
        :return: None
        """
        start, end = dates
        logger.info("Backscraping for date range %s %s", start, end)
        self.url = self._make_search_url(start, end)
        self.html = await self._download()
        self._process_html()
