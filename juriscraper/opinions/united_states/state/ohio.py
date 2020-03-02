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
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
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
        self.base_path = '//tr[contains(.//a/@href, ".pdf")]/td[2][string-length(normalize-space(text())) > 1]/./..'
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=self.backwards_days)


    def _download(self, request_dict={}):
        self.set_local_variables()
        assert self.start_date.year == self.end_date.year, "Ohio can not wrap years"
        pg = 2
        r = self.request["session"].get(self.url)
        soup = html.fromstring(r.text)
        self.data["__VIEWSTATE"] = soup.xpath('//*[@id="__VIEWSTATE"]/@value')[
            0
        ]
        self.data["__EVENTVALIDATION"] = soup.xpath(
            '//*[@id="__EVENTVALIDATION"]/@value'
        )[0]

        response = self.request["session"].post(
            "http://www.supremecourtofohio.gov/rod/docs/", data=self.data
        )

        soup = html.fromstring(response.text)
        orders = soup.xpath(self.base_path)

        del self.data["ctl00$MainContent$btnSubmit"]

        while soup.xpath('//a[contains(.//@href, "Page$%s\'")]' % pg):
            self.data["__EVENTTARGET"] = "ctl00$MainContent$gvResults"
            self.data["__EVENTARGUMENT"] = "Page$%s" % pg
            self.data["__VIEWSTATE"] = soup.xpath(
                '//*[@id="__VIEWSTATE"]/@value'
            )[0]
            self.data["__EVENTVALIDATION"] = soup.xpath(
                '//*[@id="__EVENTVALIDATION"]/@value'
            )[0]
            next_page = self.request["session"].post(self.url, data=self.data)
            if convert_date_string(orders[0].xpath(".//td")[5].text_content().strip()) <= self.end_date:
                pg = 999

            soup = html.fromstring(next_page.text)
            orders = orders + soup.xpath(self.base_path)
            pg = pg + 1

            if convert_date_string(orders[-1].xpath(".//td")[5].text_content().strip()) < self.start_date:
                pg = 999

        return [x for x in orders if self.end_date >= convert_date_string(x.xpath(".//td")[5].text_content().strip()) >= self.start_date]

    def _get_case_names(self):
        return [
            row.xpath(".//td")[0].text_content().strip() for row in self.html
        ]

    def _get_download_urls(self):
        return [row.xpath(".//a/@href")[0] for row in self.html]

    def _get_docket_numbers(self):
        return [
            row.xpath(".//td")[1].text_content().strip() for row in self.html
        ]

    def _get_summaries(self):
        return [
            row.xpath(".//td")[2].text_content().strip() for row in self.html
        ]

    def _get_case_dates(self):
        return [
            convert_date_string(row.xpath(".//td")[5].text_content().strip())
            for row in self.html
        ]

    def _get_neutral_citations(self):
        return [
            row.xpath(".//td")[7].text_content().strip() for row in self.html
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_judges(self):
        return [
            row.xpath(".//td")[3].text_content().strip() for row in self.html
        ]

    def set_local_variables(self):
        self.start_date = self.end_date - timedelta(days=self.backwards_days)
        self.data = {
            "__VIEWSTATEENCRYPTED": "",
            "ctl00$MainContent$ddlCourt": self.court_index,
            "ctl00$MainContent$ddlCounty": "0",
            "ctl00$MainContent$ddlDecidedYearMin": self.end_date.year,
            "ctl00$MainContent$ddlDecidedYearMax": self.start_date.year,
            "ctl00$MainContent$btnSubmit": "Submit",
            "ctl00$MainContent$ddlRowsPerPage": "200",
        }
