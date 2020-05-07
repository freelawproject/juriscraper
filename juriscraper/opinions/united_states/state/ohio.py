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
from datetime import date, datetime, timedelta
from lxml import html
from juriscraper.OpinionSiteAspx import OpinionSiteAspx
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSiteAspx):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        # Changing the page # in the url will get additional pages
        # Changing the source # (0-13) will get the 12 Courts of Appeals and
        # the Court of Claims. We do not use the "all sources" link because a
        # single day might yield more than 25 opinions and this scraper is
        # not designed to walk through multiple pages.
        self.court_index = 0
        self.year = str(date.today().year)
        self.backwards_days = 7
        self.url = "http://www.supremecourtofohio.gov/rod/docs/"
        self.court_id = self.__module__
        self.base_xp = '//tr[contains(.//a/@href, ".pdf")]/td[2][string-length(normalize-space(text())) > 1]/./..'
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=self.backwards_days)
        self.page = 2
        self.data = None
        self.html = None

    # Required by OpinionSiteAspx
    def _get_event_target(self):
        return "ctl00$MainContent$gvResults"

    # Required by OpinionSiteAspx
    def _get_data_template(self):
        return {
            "__EVENTTARGET": None,
            "__EVENTVALIDATION": None,
            "__VIEWSTATE": None,
            "__VIEWSTATEENCRYPTED": "",
            "ctl00$MainContent$ddlCounty": "0",
            "ctl00$MainContent$btnSubmit": "Submit",
            "ctl00$MainContent$ddlRowsPerPage": "200",
        }

    def _download(self, request_dict={}):
        self.start_date = self.end_date - timedelta(days=self.backwards_days)
        assert (
            self.start_date.year == self.end_date.year
        ), "Ohio can not wrap years"
        # Get the initial site
        self.method = "GET"
        self._update_html()

        # Do a post with updated data to get the opinions.
        self._update_data()
        self.method = "POST"
        self._update_html()

        orders = self.html.xpath(self.base_xp)
        del self.data["ctl00$MainContent$btnSubmit"]

        while self.html.xpath(
            '//a[contains(.//@href, "Page$%s\'")]' % self.page
        ):
            self._update_data()
            self._update_html()
            if (
                convert_date_string(
                    orders[0].xpath(".//td")[5].text_content().strip()
                )
                <= self.end_date
            ):
                pg = 999

            orders = orders + self.html.xpath(self.base_xp)
            self.page += 1

            if (
                convert_date_string(
                    orders[-1].xpath(".//td")[5].text_content().strip()
                )
                < self.start_date
            ):
                pg = 999

        self.orders = [
            x
            for x in orders
            if self.end_date
            >= convert_date_string(x.xpath(".//td")[5].text_content().strip())
            >= self.start_date
        ]
        return self.html

    def _get_case_names(self):
        return [
            row.xpath(".//td")[0].text_content().strip() for row in self.orders
        ]

    def _get_download_urls(self):
        return [row.xpath(".//a/@href")[0] for row in self.orders]

    def _get_docket_numbers(self):
        return [
            row.xpath(".//td")[1].text_content().strip() for row in self.orders
        ]

    def _get_summaries(self):
        return [
            row.xpath(".//td")[2].text_content().strip() for row in self.orders
        ]

    def _get_case_dates(self):
        return [
            convert_date_string(row.xpath(".//td")[5].text_content().strip())
            for row in self.orders
        ]

    def _get_neutral_citations(self):
        return [
            row.xpath(".//td")[7].text_content().strip() for row in self.orders
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_judges(self):
        return [
            row.xpath(".//td")[3].text_content().strip() for row in self.orders
        ]

    def _update_data(self):
        # Call the super class version, which creates a new data dict from the
        # template and fills in ASPX specific values.
        super(Site, self)._update_data()

        self.data.update(
            {
                "__EVENTARGUMENT": "Page$%s" % self.page,
                "ctl00$MainContent$ddlCourt": self.court_index,
                "ctl00$MainContent$ddlDecidedYearMin": self.end_date.year,
                "ctl00$MainContent$ddlDecidedYearMax": self.start_date.year,
            }
        )
