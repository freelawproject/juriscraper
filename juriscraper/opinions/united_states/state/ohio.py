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
 - 2021-12-28: Remove selenium by flooie
"""
from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_index = 0
        self.year = date.today().year
        self.url = "https://www.supremecourtofohio.gov/rod/docs/"
        self.court_id = self.__module__

    def _set_parameters(
        self,
        event_validation: str,
        view_state: str,
    ) -> None:
        """Set the parameters for the search

        :param: event_validation: the event validation token
        :param: view_state: the view state token
        :return: None
        """
        self.parameters = {
            "__VIEWSTATEENCRYPTED": "",
            "ctl00$MainContent$ddlCourt": f"{self.court_index}",
            "ctl00$MainContent$ddlDecidedYearMin": f"{self.year}",
            "ctl00$MainContent$ddlDecidedYearMax": f"{self.year}",
            "ctl00$MainContent$ddlCounty": "0",
            "ctl00$MainContent$btnSubmit": "Submit",
            "ctl00$MainContent$ddlRowsPerPage": "50",
            "__EVENTVALIDATION": event_validation,
            "__VIEWSTATE": view_state,
        }
        self.url = "https://www.supremecourt.ohio.gov/rod/docs/"
        self.method = "POST"

    def _process_html(self) -> None:
        """Process the HTML and extract the data"""
        if not self.test_mode_enabled():
            event_validation = self.html.xpath(
                "//input[@id='__EVENTVALIDATION']"
            )[0].get("value")
            view_state = self.html.xpath("//input[@id='__VIEWSTATE']")[0].get(
                "value"
            )
            self._set_parameters(
                event_validation,
                view_state,
            )
            self.html = self._download()

        # Skip the header rows and the footer rows
        for row in self.html.xpath(
            ".//table[@id='MainContent_gvResults']//tr"
        )[3:-2]:
            # Filter out the case announcements and rulings (ie non-opinions)
            if not row.xpath(".//td[2]//text()")[0].strip():
                continue
            self.cases.append(
                {
                    "judge": row.xpath(".//td[4]//text()")[0],
                    "docket": row.xpath(".//td[2]//text()")[0],
                    "date": row.xpath(".//td[6]//text()")[0],
                    "name": row.xpath(".//a/text()")[0],
                    "url": row.xpath(".//a")[0].get("href"),
                    "citation": row.xpath(".//td[8]//text()")[0],
                    "summary": row.xpath(".//td[3]//text()")[0],
                    "status": "Published",
                }
            )
