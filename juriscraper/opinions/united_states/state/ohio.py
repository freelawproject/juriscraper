"""Scraper for the Supreme Court of Ohio
CourtID: ohio
Court Short Name: Ohio
Author: Andrei Chelaru
Reviewer: mlr
History:
 - Stubbed out by Brian Carver
 - 2014-07-30: Finished by Andrei Chelaru
 - 2015-07-31: Redone by mlr to use ghost driver. Alas, their site used to be
               great, but now it's terribly frustrating.
"""
from datetime import date, datetime

from lxml import html
from lxml.html import tostring

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.string_utils import clean_if_py3
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_index = 0
        self.year = str(date.today().year)
        self.url = "https://www.supremecourtofohio.gov/rod/docs/"
        self.court_id = self.__module__
        self.data = {
            "__VIEWSTATEENCRYPTED": "",
            "ctl00$MainContent$ddlCourt": f"{self.court_index}",
            "ctl00$MainContent$ddlDecidedYearMin": f"{self.year}",
            "ctl00$MainContent$ddlDecidedYearMax": f"{self.year}",
            "ctl00$MainContent$ddlCounty": "0",
            "ctl00$MainContent$btnSubmit": "Submit",
            "ctl00$MainContent$ddlRowsPerPage": "50",
        }

    def _process_html(self):
        self.data["__EVENTVALIDATION"] = self.html.xpath(
            "//input[@id='__EVENTVALIDATION']"
        )[0].get("value")
        self.data["__VIEWSTATE"] = self.html.xpath(
            "//input[@id='__VIEWSTATE']"
        )[0].get("value")
        self.url = "https://www.supremecourt.ohio.gov/rod/docs/"
        response = self.request["session"].post(self.url, data=self.data)
        self.html = html.fromstring(response.text)
        for row in self.html.xpath(
            ".//table[@id='MainContent_gvResults']//tr"
        )[3:-2]:
            self.cases.append(
                {
                    "judge": row.xpath(".//td[4]//text()")[0],
                    "docket": row.xpath(".//td[2]//text()")[0],
                    "date": row.xpath(".//td[6]//text()")[0],
                    "name": row.xpath(".//a/text()")[0],
                    "url": row.xpath(".//a")[0].get("href"),
                    "status": "Published",
                    "neutral_citation": row.xpath(".//td[8]//text()")[0],
                    "summary": row.xpath(".//td[3]//text()")[0],
                }
            )
