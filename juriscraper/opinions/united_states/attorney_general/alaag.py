"""
Scraper for Alabama AG
CourtID: alaag
Court Short Name: Ala AG
Author: William E. Palin
History:
 - 2023-01-29: Created.
"""
import re
from datetime import date, timedelta

from lxml.html import fromstring

from juriscraper.lib.html_utils import get_html_parsed_text
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.alabamaag.gov/opinions"
        self.td = date.today()
        today = self.td.strftime("%Y-%m-%d")
        last_month = (self.td - timedelta(days=61)).strftime("%Y-%m-%d")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15",
        }
        self.parameters = {
            "ctl00$ContentFullBody$ContentBody$ucSearchOpinions1$ScriptManager1": "ctl00$ContentFullBody$ContentBody$ucSearchOpinions1$UpdatePanel1|ctl00$ContentFullBody$ContentBody$ucSearchOpinions1$btnSearch",
            "ctl00$txtSearch": "",
            "ctl00$ContentFullBody$ContentBody$ucSearchOpinions1$txtSearchName": "20",
            "ctl00$ContentFullBody$ContentBody$ucSearchOpinions1$rbdSearchType": "1",
            "ctl00$ContentFullBody$ContentBody$ucSearchOpinions1$txtSearchAfterDate": last_month,
            "ctl00$ContentFullBody$ContentBody$ucSearchOpinions1$txtSearchBeforeDate": today,
            "__LASTFOCUS": "",
            "__VIEWSTATEENCRYPTED": "",
            "__ASYNCPOST": "true",
            "ctl00$ContentFullBody$ContentBody$ucSearchOpinions1$btnSearch": "Search",
        }

    def _download(self, request_dict={}):
        """Custom download method

        :param request_dict: Empty dict
        :return: HTML content
        """
        if self.test_mode_enabled():
            self.html = get_html_parsed_text(open(self.url).read())
            return self.html
        if self.html:
            self._update_query_params()
            r = self.request["session"].post(
                self.url, headers=self.headers, data=self.parameters
            )
            self.html = fromstring(r.text)
        else:
            html = super()._download(request_dict)
            return html

    def _update_query_params(self):
        """Update the query parameters for next page

        :return: None
        """
        vs_xpath = "//input[@name='__VIEWSTATE']"
        ev_xpath = "//input[@name='__EVENTVALIDATION']"
        vsg_xpath = "//input[@name='__VIEWSTATEGENERATOR']"

        self.parameters["__VIEWSTATE"] = self.html.xpath(vs_xpath)[0].attrib[
            "value"
        ]
        self.parameters["__EVENTVALIDATION"] = self.html.xpath(ev_xpath)[
            0
        ].attrib["value"]
        self.parameters["__VIEWSTATEGENERATOR"] = self.html.xpath(vsg_xpath)[
            0
        ].attrib["value"]

    def _process_html(self):
        """Process the html

        :return: None
        """
        self._download()
        for row in self.html.xpath(".//tr/td/.."):
            if not row.xpath(".//td/a/@href"):
                continue
            docket = re.sub(
                r"\r\n", "", row.xpath(".//td[2]")[0].text_content()
            )
            self.cases.append(
                {
                    "name": f"Untitled AG Opinion: {docket.strip()}",
                    "docket": docket.strip(),
                    "url": row.xpath(".//td/a/@href")[0],
                    "summary": row.xpath(".//td[3]")[0].text_content().strip(),
                    "date": row.xpath(".//td[4]")[0].text_content().strip(),
                }
            )
