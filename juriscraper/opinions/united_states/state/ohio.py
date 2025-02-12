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
from juriscraper.lib.utils import backscrape_over_paginated_results
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    days_interval = 50 * 365  # get the formatted input dates
    first_opinion_date = date(1992, 1, 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

        # to be used as POST data
        self.year = date.today().year
        self.rows_per_page = "50"
        self.court_index = 0

        # Home https://www.supremecourt.ohio.gov/Rod/docs/Default.aspx
        self.url = f"https://www.supremecourt.ohio.gov/rod/docs/?HideTopicsAndIssuesColumn=False&Sort=&PageSize=50&Source={self.court_index}"
        self.make_backscrape_iterable(kwargs)
        self.is_first_request = True

    def _process_html(self) -> None:
        """Process the HTML and extract the data

        :return: None
        """
        # Load the page once to populate hidden inputs; set parameters and
        # do the actual query
        if not self.test_mode_enabled() and self.is_first_request:
            self.set_parameters()
            self.html = self._download()
            self.is_first_request = False

        for row in self.html.xpath(
            ".//table[@id='MainContent_gvResults']//tr[not(.//a[contains(@href, 'javascript')])]"
        ):
            # Filter out the case announcements and rulings (ie non-opinions)
            docket = row.xpath(".//td[2]//text()")[0].strip()
            name = row.xpath(".//a/text()")[0]
            if not docket:
                logger.debug("Skipping row with name '%s'", name.strip())
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
                "date": row.xpath(".//td[6]//text()")[0].strip(),
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

    def set_parameters(self, page_number: str = "") -> None:
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
            "ctl00$MainContent$ddlRowsPerPage": self.rows_per_page,
            "__EVENTVALIDATION": event_validation[0].get("value"),
            "__VIEWSTATE": view_state[0].get("value"),
        }

        if page_number:
            self.parameters.update(
                {
                    "__EVENTARGUMENT": f"Page${page_number}",
                    "__EVENTTARGET": "ctl00$MainContent$gvResults",
                }
            )
        else:
            self.parameters["ctl00$MainContent$btnSubmit"] = "Submit"

        self.method = "POST"

    def _download_backwards(self, d: tuple[date]) -> None:
        """Filter site to get older records

        There is max of 1000 results returned per search; so it's better
        to backscrape per year, even when it would be possible to try the
        whole range in a single request
        """
        logger.info("Backscraping date range %s %s", *d)
        start_date, end_date = d
        self.rows_per_page = "200"
        self.year = str(start_date.year)
        self.url = self.url.replace(
            "PageSize=50", f"PageSize={self.rows_per_page}"
        )

        # reset start state
        self.is_first_request = True
        self.method = "GET"

        cases = backscrape_over_paginated_results(
            1,
            100,
            start_date,
            end_date,
            "%m/%d/%Y",
            self,
            self.set_parameters_by_page,
        )
        self.cases = cases

    @staticmethod
    def set_parameters_by_page(page: int, site) -> None:
        """Function to set the page number inside
        `backscrape_over_paginated_results`

        :param page: the page number
        :param site: the site object
        :return None
        """
        if site.is_first_request:
            logger.info("First request; skipping pagination params")
            return
        site.set_parameters(str(page))

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        super().make_backscrape_iterable(kwargs)
        start_date = self.back_scrape_iterable[0][0]
        end_date = self.back_scrape_iterable[0][-1]

        self.back_scrape_iterable = []
        # Generate a tuple for each year
        current_date = start_date

        while current_date <= end_date:
            current_year = current_date.year
            year_start = date(current_year, 1, 1)
            year_end = date(current_year, 12, 31)

            range_start = max(current_date, year_start)
            range_end = min(end_date, year_end)

            self.back_scrape_iterable.append((range_start, range_end))
            current_date = date(current_year + 1, 1, 1)
