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

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_index = 0
        self.year = date.today().year
        self.url = f"https://www.supremecourt.ohio.gov/rod/docs/?HideTopicsAndIssuesColumn=False&Sort=&PageSize=50&Source={self.court_index}"
        self.court_id = self.__module__

    def _set_parameters(self) -> None:
        """Set the parameters for the search

        :return: None
        """
        event_validation = self.html.xpath("//input[@id='__EVENTVALIDATION']")
        view_state = self.html.xpath("//input[@id='__VIEWSTATE']")
        self.parameters = {
            "__VIEWSTATEENCRYPTED": "",
            "ctl00$MainContent$ddlCourt": f"{self.court_index}",
            "ctl00$MainContent$ddlDecidedYearMin": f"{self.year}",
            "ctl00$MainContent$ddlDecidedYearMax": f"{self.year}",
            "ctl00$MainContent$ddlCounty": "0",
            "ctl00$MainContent$btnSubmit": "Submit",
            "ctl00$MainContent$ddlRowsPerPage": "50",
            "__EVENTVALIDATION": event_validation[0].get("value"),
            "__VIEWSTATE": view_state[0].get("value"),
        }
        self.method = "POST"

    def _process_html(self) -> None:
        """Process the HTML and extract the data

        :return: None
        """
        if not self.test_mode_enabled():
            self._set_parameters()
            self.html = self._download()

        for row in self.html.xpath(
            ".//table[@id='MainContent_gvResults']//tr[not(.//a[contains(@href, 'javascript')])]"
        ):
            # Filter out the case announcements and rulings (ie non-opinions)
            docket = row.xpath(".//td[2]//text()")[0].strip()
            name = row.xpath(".//a/text()")[0]
            if not docket:
                logger.info("Skipping row with name '%s'", name.strip())
                continue

            judge = row.xpath(".//td[4]//text()")[0]
            per_curiam = False
            if "per curiam" in judge.lower():
                judge = ""
                per_curiam = True

            citation_or_county = row.xpath(".//td[5]//text()")[0].strip()
            web_cite = row.xpath(".//td[8]//text()")[0]
            case = {
                "docket": docket,
                "name": name,
                "judge": judge,
                "per_curiam": per_curiam,
                "summary": row.xpath(".//td[3]//text()")[0],
                "date": row.xpath(".//td[6]//text()")[0],
                "url": row.xpath(".//a")[0].get("href"),
                "citation": web_cite,
                "status": "Published",
            }

            # Looking for lagged citations like: '175 Ohio St.3d 155'
            # For Supreme Court cases
            if self.court_index == 0:
                citation = ""
                if web_cite not in citation_or_county:
                    citation = citation_or_county
                case["parallel_citation"] = citation
            elif "ohioctapp" in self.court_id:
                # For ohioctapp cases. This will be important to disambiguate
                # docket numbers, which may be repeated across districts
                case["lower_court"] = f"{citation_or_county} County Court"

            if (
                f"https://www.supremecourt.ohio.gov/rod/docs/pdf/{self.court_index}/"
                not in case["url"]
            ):
                logger.warning("Wrong appellate page detected.")
                continue
            self.cases.append(case)
