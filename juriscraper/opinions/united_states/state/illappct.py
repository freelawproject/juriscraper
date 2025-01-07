"""
Scraper for Illinois Appellate Court
CourtID: illappct
Author: Krist Jin
History:
  2013-08-18: Created.
  2014-07-17: Updated by mlr to remedy InsanityException.
  2021-11-02: Updated by satsuki-chan: Updated to new page design.
  2022-01-21: Updated by satsuki-chan: Added validation when citation is missing.
"""

import re
from datetime import datetime

from lxml import html

from juriscraper.opinions.united_states.state import ill


class Site(ill.Site):
    days_interval = 10
    first_opinion_date = datetime(1996, 9, 3)
    court_filter = "All Appellate Court"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = ("https://www.illinoiscourts.gov/top-level-opinions/")
        self.docket_re = r"(?P<citation>\d{4}\s+IL App\s+(\((?P<district>\d+)\w{1,2}\)\s+)?(?P<docket>\d+\w{1,2})-?U?[BCD]?)"

    def _get_docket(self, match: re.Match) -> str:
        """Builds docket_number from a regex match

        :param match: a regex match object
        :return: docket_number
        """
        raw_docket = match.group("docket")
        district = match.group("district")
        return f"{district}-{raw_docket[0:2]}-{raw_docket[2:]}"

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self._request_url_get(self.url)
        self._post_process_response()
        temp_html = self._return_response_text_object()
        hdn = temp_html.xpath("//div[@class='aspNetHidden']")[0]
        views_state = hdn.xpath("//input[@id='__VIEWSTATE']/@value")[0]
        flag = True
        i = 1
        while flag:
            self.parameters = {
                "__EVENTTARGET": "ctl00$ctl04$gvDecisions",
                "__EVENTARGUMENT": f"Page${i}",
                "__LASTFOCUS": "",
                "__VIEWSTATE": views_state,
                "__VIEWSTATEGENERATOR": "66677877",
                "ctl00$header$search$txtSearch": "",
                "ctl00$ctl04$txtFilterName": "",
                "ctl00$ctl04$txtFilterPostingFrom": "12/16/2014",
                "ctl00$ctl04$txtFilterPostingTo": "12/16/2025",
                "ctl00$ctl04$ddlFilterFilingDate": "Custom Date Range",
                "ctl00$ctl04$txtFilterFilingFrom": start_date.strftime("%m/%d/%Y"),
                "ctl00$ctl04$txtFilterFilingTo": end_date.strftime("%m/%d/%Y"),
                "ctl00$ctl04$ddlFilterCourtType": "All Appellate Court",
                "ctl00$ctl04$ddlFilterType": "",
                "ctl00$ctl04$ddlFilterStatus": "",
                "ctl00$ctl04$hdnSortField": "FilingDate",
                "ctl00$ctl04$hdnSortDirection": "DESC"
            }
            self.method = 'POST'
            self.parse()
            next_div = self.html.xpath('//tr[@class="pagenation"]//table/tr')[0]
            last_td = next_div.xpath('td[last()]')[0]
            check_last = html.tostring(last_td, pretty_print=True).decode()
            self.downloader_executed = False
            i = i + 1
            if not check_last.__contains__('href="javascript:__doPostBack'):
                flag=False
        return 0

    def get_court_name(self):
        return "Illinois Appellate Court"

    def get_class_name(self):
        return "illappct"
