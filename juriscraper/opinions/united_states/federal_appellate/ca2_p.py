"""Scraper for Second Circuit
CourtID: ca2
Contact:
  Webmaster@ca2.uscourts.gov ('Calendar Team' handles updates, and is responsive)
  ecfhelpdesk@ca2.uscourts.gov
  Shane_Clouden@ca2.uscourts.gov

History:
  2026-04-27: site migrated from the IsysWeb endpoint to a dtSearch
  POST endpoint #1919.
"""

from datetime import date, datetime, timedelta
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://ww3.ca2.uscourts.gov"
    search_url = urljoin(base_url, "/dtSearch/dtisapi6.dll")
    # The dtSearch index ID for Opinions. The companion ID for Summary
    # Orders is `*{aad0964f04f3e9c420e057fd415efe0c} SUM` (see ca2_u).
    index = "*{aa12e167958cdbcaa709fa14b9161a4a} OPN"
    first_opinion_date = datetime(2007, 1, 1)
    days_interval = 15

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.search_url
        self.method = "POST"
        self.status = "Published"

        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=self.days_interval)
        self._update_parameters()
        self.make_backscrape_iterable(kwargs)

    def _update_parameters(self) -> None:
        """Build the POST body matching the form on /decisions.html.

        The dtSearch engine expects the date range both as the
        StartDate/EndDate inputs and embedded in the `fileConditions`
        xfilter expression (the form's JS keeps both in sync).
        """
        date_filter = (
            f'xfilter(date "{self.start_date:%Y/%m/%d}'
            f'~~{self.end_date:%Y/%m/%d}")'
        )
        self.parameters = {
            "index": self.index,
            "request": "",
            "searchType": "allwords",
            "cmd": "search",
            "SearchForm": "%%SearchForm%%",
            "dtsPdfWh": "*",
            "OrigSearchForm": "/decisions.html",
            "autoStopLimit": "5000",
            "pageSize": "1000",
            "sort": "date",
            "StartDate": self.start_date.strftime("%Y-%m-%d"),
            "EndDate": self.end_date.strftime("%Y-%m-%d"),
            "fileConditions": date_filter,
            "booleanConditions": "",
        }

    def _process_html(self) -> None:
        for row in self.html.xpath('//table[@class="ResultsTable"]/tr'):
            anchor = row.xpath('.//td[@class="ResultsItemLeft"]/a')
            if not anchor:
                logger.warning("ca2: row without anchor, skipping")
                continue
            url = urljoin(self.base_url, anchor[0].get("href", "").strip())
            docket = anchor[0].text_content().strip()

            right = row.xpath('.//td[@class="ResultsItemRight"]')[0]
            fields = self._parse_right_cell(right)
            posted = fields.get("Date Posted")
            caption = fields.get("Caption")
            if not (url and docket and posted and caption):
                logger.warning(
                    "ca2: incomplete row docket=%r url=%r posted=%r caption=%r",
                    docket,
                    url,
                    posted,
                    caption,
                )
                continue

            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": titlecase(caption),
                    "date": posted,
                }
            )

    @staticmethod
    def _parse_right_cell(cell) -> dict:
        """Pull `Date Posted` and `Caption` from the right TD.

        The cell looks like:
            <B>Date Posted: </B>4/23/2026<BR>
            <B>Caption: </B>Richardson v. ...<BR>
            <B>Type: </B>/decisions/OPN<BR>
        Each <b> label's value lives in its `.tail`.
        """
        out: dict[str, str] = {}
        for b in cell.iter("b"):
            label = (b.text or "").strip().rstrip(":").strip()
            value = (b.tail or "").strip()
            if label:
                out[label] = value
        return out

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        self.start_date, self.end_date = dates
        self._update_parameters()
        self.html = await self._download()
        if self.html is not None:
            self._process_html()
