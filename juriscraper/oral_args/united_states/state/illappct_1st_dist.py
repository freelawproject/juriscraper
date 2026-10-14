"""
CourtID: illappct
Court Short Name: Ill. App. Ct.
Author: Rebecca Fordon
Reviewer: Mike Lissner
History:
* 2016-06-23: Created by Rebecca Fordon
* 2022-05-18: Updated by William E. Palin
"""

from datetime import timedelta

from dateutil.utils import today
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.illinoiscourts.gov/courts/appellate-court/oral-argument-audio/"
        self.method = "POST"
        self.today = today().strftime("%m/%d/%Y")
        self.earlier = (today() - timedelta(days=30)).strftime("%m/%d/%Y")
        self.district = "1st"
        self._set_parameters()

    def _set_parameters(self) -> None:
        self.parameters = {
            "__EVENTTARGET": "ctl00$ctl04$ddlFilterDistrict",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATEGENERATOR": "66677877",
            "ctl00$header$search$txtSearch": "",
            "ctl00$ctl04$txtFilterName": "",
            "ctl00$ctl04$ddlFilterDate": "Custom Date Range",
            "ctl00$ctl04$txtFilterDateFrom": self.earlier,
            "ctl00$ctl04$txtFilterDateTo": self.today,
            "ctl00$ctl04$ddlFilterDistrict": self.district,
            "ctl00$ctl04$hdnSortField": "ArgumentDate",
            "ctl00$ctl04$hdnSortDirection": "DESC",
        }

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(
            './/table[@id="ctl04_gvArguments"]/tr[not(th)]'
        )
        for row in rows:
            urls: list[str] = row.xpath(".//a/@data-audio")
            if not bool(urls):
                logger.warning("Skipping row with no audio file to download")
                continue

            url = urls[0].replace(" ", "%20")
            span_elements = row.findall(".//span")
            spans = [span.text_content().strip() for span in span_elements]
            if len(spans) < 4:
                logger.warning(
                    "Skipping row with insufficient data: expected at least 4 values, got %s",
                    "-".join(spans),
                )
                continue
            date, _, docket, name, *others = spans
            if bool(others):
                docket, name = name, others[0]
            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "name": name,
                    "url": url,
                }
            )
