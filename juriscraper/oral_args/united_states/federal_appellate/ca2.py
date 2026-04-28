"""Scraper for Second Circuit Oral Arguments
CourtID: ca2
Author: MLR
Reviewer: MLR
Contact:
  Webmaster@ca2.uscourts.gov ('Calendar Team' handles updates, and is responsive)
  ecfhelpdesk@ca2.uscourts.gov
  Shane_Clouden@ca2.uscourts.gov
History:
  2016-09-09: Created by MLR
  2023-11-21: Fixed by flooie
  2023-12-11: Fixed by quevon24
  2026-01-21: Fixed by Luis-manzur
  2026-04-28: site migrated from the IsysWeb endpoint to a dtSearch
    POST endpoint #1926.
"""

from datetime import date, datetime, timedelta
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.opinions.united_states.federal_appellate.ca2_p import (
    Site as Ca2OpinionSite,
)
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    base_url = "https://ww3.ca2.uscourts.gov"
    search_url = urljoin(base_url, "/dtSearch/dtisapi6.dll")
    # The dtSearch index ID for Oral Argument audio (see ca2_p for the
    # opinion / summary order indexes).
    index = "*{aaa02d786aee6c9336b7efb2e231863a} audio"
    # `make_backscrape_iterable` looks for `first_opinion_date` regardless
    # of whether this is an opinion or oral-argument scraper, so reuse
    # that attribute name even though semantically it's the first oral arg.
    first_opinion_date = datetime(2016, 1, 1)
    days_interval = 15

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self.search_url
        self.method = "POST"

        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=self.days_interval)
        self._update_parameters()
        self.make_backscrape_iterable(kwargs)

    def _update_parameters(self) -> None:
        """Build the POST body matching the form on /oral_arguments.html.

        Mirrors the opinion form (`ca2_p`): the dtSearch engine wants the
        date range both as StartDate/EndDate and embedded in the
        `fileConditions` xfilter expression.
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
            "OrigSearchForm": "/oral_arguments.html",
            "autoStopLimit": "5000",
            "pageSize": "1000",
            "sort": "Date",
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
            docket = Ca2OpinionSite._clean(anchor[0].text_content())

            right = row.xpath('.//td[@class="ResultsItemRight"]')[0]
            fields = Ca2OpinionSite._parse_right_cell(right)
            argued = fields.get("Date Argued")
            caption = fields.get("Caption")
            if not (url and docket and argued and caption):
                logger.warning(
                    "ca2: incomplete row docket=%r url=%r argued=%r caption=%r",
                    docket,
                    url,
                    argued,
                    caption,
                )
                continue

            self.cases.append(
                {
                    "url": url,
                    "docket": docket,
                    "name": titlecase(caption),
                    "date": argued,
                }
            )

    async def _download_backwards(self, dates: tuple[date, date]) -> None:
        self.start_date, self.end_date = dates
        self._update_parameters()
        self.html = await self._download()
        if self.html is not None:
            self._process_html()
