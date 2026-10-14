"""
CourtID: ill
Court Short Name: Ill.
Author: Rebecca Fordon
Reviewer: Mike Lissner
History:
* 2016-06-22: Created by Rebecca Fordon
* 2022-05-18: Updated by William E. Palin
"""

from datetime import timedelta

from dateutil.utils import today
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.string_utils import CaseNameTweaker, clean_string
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
        self.url = "https://www.illinoiscourts.gov/courts/supreme-court/oral-argument-audio-and-video/"
        self.method = "POST"
        self.today = today().strftime("%m/%d/%Y")
        self.earlier = (today() - timedelta(days=30)).strftime("%m/%d/%Y")
        self._set_parameters()

    def _set_parameters(self) -> None:
        self.parameters = {
            "__EVENTTARGET": "ctl00$ctl04$txtFilterDateFrom",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATEGENERATOR": "66677877",
            "ctl00$header$search$txtSearch": "",
            "ctl00$ctl04$txtFilterName": "",
            "ctl00$ctl04$ddlFilterDate": "Custom Date Range",
            "ctl00$ctl04$txtFilterDateFrom": self.earlier,
            "ctl00$ctl04$txtFilterDateTo": self.today,
            "ctl00$ctl04$hdnSortField": "ArgumentDate",
            "ctl00$ctl04$hdnSortDirection": "DESC",
        }

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        for row in self.html.findall(".//tr")[1:]:
            audio_anchor: list[str] = row.xpath(".//a/@data-audio")
            if not bool(audio_anchor):
                logger.warning(
                    "Row has no audio anchor '%s'",
                    clean_string(row.text_content()),
                )
                continue

            self.cases.append(
                {
                    "date": row.xpath(".//td[1]/span[1]/text()")[0],
                    "docket": row.xpath(".//td[2]/span[1]/text()")[0],
                    "name": row.xpath(".//td[3]/span[1]/text()")[0],
                    "url": audio_anchor[0],
                }
            )
