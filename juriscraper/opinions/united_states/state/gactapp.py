# Scraper for Georgia Appeals Court
# CourtID: gactapp
# Court Short Name: gactapp
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 25 July 2014

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = date(2012, 3, 30)
    days_interval = 7

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        last_week = today - timedelta(days=7)
        self.status = "Published"

        # default most recent week
        self.url = (
            "https://www.gaappeals.us/wp-content/themes/benjamin/docket/"
            f"docketdate/results_all.php?OPstartDate={last_week:%Y-%m-%d}&OPendDate={today:%Y-%m-%d}&submit=Start+Opinions+Search"
        )

        # build backscrape iterable
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        for row in self.html.xpath("//tr")[::-1][:-1]:
            docket, name, date_el, disposition, _, url_el = row.xpath(".//td")
            url = url_el.xpath(".//a")[0].get("href")
            if url == "https://efast.gaappeals.us/download?filingId=":
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

    def _download_backwards(self, date_range: str) -> None:
        """Backscrape one weekly date range (start,end)."""
        start, end = date_range.split(",")
        self.url = (
            "https://www.gaappeals.us/wp-content/themes/benjamin/docket/"
            f"docketdate/results_all.php?OPstartDate={start}&OPendDate={end}&submit=Start+Opinions+Search"
        )

        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict[str, str]) -> None:
        """Generate weekly date ranges from backscrape_start → backscrape_end."""
        start_str = kwargs.get("backscrape_start")
        end_str = kwargs.get("backscrape_end")

        if not start_str or not end_str:
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
