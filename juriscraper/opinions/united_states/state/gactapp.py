# Scraper for Georgia Appeals Court
# CourtID: gactapp
# Court Short Name: gactapp
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 25 July 2014

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.lib.type_utils import BackscrapeOptions
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear[str]):
    first_opinion_date = date(2012, 3, 30)
    days_interval = 7

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[str]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        last_week = today - timedelta(days=7)
        self.status = "Published"

        # default most recent week
        self.url = (
            "https://www.gaappeals.gov/wp-content/themes/benjamin/docket/"
            f"docketdate/results_all.php?OPstartDate={last_week:%Y-%m-%d}&OPendDate={today:%Y-%m-%d}&submit=Start+Opinions+Search"
        )

        # build backscrape iterable
        self.make_backscrape_iterable(kwargs)

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath("//tr")[::-1][:-1]
        for row in rows:
            docket, name, date_el, disposition, _, url_el = row.findall(
                ".//td"
            )
            url = url_el.findall(".//a")[0].attrib["href"]
            if url == "https://efast.gaappeals.gov/download?filingId=":
                logger.error("Skipping doc with empty filingId: %s", url)
                continue
            self.cases.append(
                {
                    "docket": docket.text_content().strip(),
                    "name": titlecase(name.text_content().strip()),
                    "date": date_el.text_content().strip(),
                    "disposition": disposition.text_content().strip().title(),
                    "url": url,
                }
            )

    @override
    async def _download_backwards(self, date_range: str) -> None:
        """Backscrape one weekly date range (start,end)."""
        start, end = date_range.split(",")
        self.url = (
            "https://www.gaappeals.gov/wp-content/themes/benjamin/docket/"
            f"docketdate/results_all.php?OPstartDate={start}&OPendDate={end}&submit=Start+Opinions+Search"
        )

        self.html = await self._download()
        self._process_html()

    @override
    def make_backscrape_iterable(self, kwargs: BackscrapeOptions) -> None:
        """Generate weekly date ranges from backscrape_start → backscrape_end."""
        start_str = kwargs.get("backscrape_start")
        end_str = kwargs.get("backscrape_end")

        if not bool(start_str) or not bool(end_str):
            # Default: scrape past 6 months
            end_date = date.today()
            start_date = end_date - relativedelta(months=6)
        else:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

        date_ranges = []
        current = start_date
        while current <= end_date:
            week_end = min(current + timedelta(days=7), end_date)
            date_ranges.append(f"{current:%Y-%m-%d},{week_end:%Y-%m-%d}")
            current = week_end + timedelta(days=1)

        self.back_scrape_iterable = date_ranges
