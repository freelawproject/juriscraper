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

from datetime import date, datetime, timedelta

from bs4 import BeautifulSoup
from lxml import etree

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_number = 1
        self.max_page_num = -1
        self.court_index = 0
        self.year = date.today().year
        self.url = "https://www.supremecourt.ohio.gov/rod/docs/"
        self.court_id = self.__module__
    def _set_parameters(self,start_year,end_year) -> None:
        event_validation = self.html.xpath("//input[@id='__EVENTVALIDATION']")
        view_state = self.html.xpath("//input[@id='__VIEWSTATE']")
        self.parameters = {
            "__VIEWSTATEENCRYPTED": "",
            "ctl00$MainContent$ddlCourt": f"{self.court_index}",
            "ctl00$MainContent$ddlDecidedYearMin": str(start_year),
            "ctl00$MainContent$ddlDecidedYearMax": str(end_year),
            "ctl00$MainContent$ddlCounty": "0",
            "ctl00$MainContent$btnSubmit": "Submit",
            "ctl00$MainContent$ddlRowsPerPage": "50",
            "__EVENTVALIDATION": event_validation[0].get("value"),
            "__VIEWSTATE": view_state[0].get("value"),
        }
        self.method = "POST"

    def _set_parameters1(self,start_year,end_year) -> None:
        event_validation = self.html.xpath("//input[@id='__EVENTVALIDATION']")
        view_state = self.html.xpath("//input[@id='__VIEWSTATE']")
        self.parameters = {
            "__EVENTTARGET": "ctl00$MainContent$gvResults",
            "__VIEWSTATEENCRYPTED": "",
            "__EVENTARGUMENT":f"Page${self.page_number}",
            "ctl00$MainContent$ddlCourt": f"{self.court_index}",
            "ctl00$MainContent$ddlDecidedYearMin": str(start_year),
            "ctl00$MainContent$ddlDecidedYearMax": str(end_year),
            "ctl00$MainContent$ddlCounty": "0",
            "ctl00$MainContent$ddlRowsPerPage": "50",
            "__EVENTVALIDATION": event_validation[0].get("value"),
            "__VIEWSTATE": view_state[0].get("value"),
        }
        self.method = "POST"

    def _set_parameters2(self,start_year,end_year) -> None:
        event_validation = self.html.xpath("//input[@id='__EVENTVALIDATION']")
        view_state = self.html.xpath("//input[@id='__VIEWSTATE']")
        self.parameters = {
            "__EVENTTARGET": "ctl00$MainContent$gvResults",
            "__VIEWSTATEENCRYPTED": "",
            "__EVENTARGUMENT":"Page$Last",
            "ctl00$MainContent$ddlCourt": f"{self.court_index}",
            "ctl00$MainContent$ddlDecidedYearMin": str(start_year),
            "ctl00$MainContent$ddlDecidedYearMax": str(end_year),
            "ctl00$MainContent$ddlCounty": "0",
            "ctl00$MainContent$ddlRowsPerPage": "50",
            "__EVENTVALIDATION": event_validation[0].get("value"),
            "__VIEWSTATE": view_state[0].get("value"),
        }
        self.method = "POST"


    def _process_html(self,start_date,end_date) -> None:
        """Process the HTML and extract the data"""
        if not self.test_mode_enabled():
            logger.info("test mode is disabled, now setting parameters")
            if self.page_number<=1:
                self._set_parameters(start_date,end_date)
            # elif self.page_number == self.max_page_num:
            #     print(f"calling url for last page now and the current and last page number is {self.page_number} and {self.max_page_num}")
            #     self._set_parameters2(start_date,end_date)
            else:
                self._set_parameters1(start_date,end_date)
            self.html = self._download()
            soup = BeautifulSoup(etree.tostring(self.html, pretty_print=True).decode("utf-8"), 'html.parser')

            table = soup.find("table", {"id": "MainContent_gvResults"})
            first_data_row = table.find_all("tr")[
                1]
            row_data = [cell.get_text(strip=True) for cell in
                        first_data_row.find_all("td")]
            curr_page = row_data[-1]
            if "Ohio" in curr_page :
                curr_page=1
            if curr_page != ">>" and int(curr_page) > self.max_page_num :
                    self.max_page_num=int(curr_page)


        for row in self.html.xpath(
            ".//table[@id='MainContent_gvResults']//tr[not(.//a[contains(@href, 'javascript')])]"
        ):
            # Filter out the case announcements and rulings (ie non-opinions)
            docket = row.xpath(".//td[2]//text()")[0].strip()
            name = row.xpath(".//a/text()")[0]
            # if not docket:
            #     logger.info("Skipping row with name '%s'", name)
            #     continue

            judge = row.xpath(".//td[4]//text()")[0]
            per_curiam = False
            if "per curiam" in judge.lower():
                judge = ""
                per_curiam = True

            citation_or_county = row.xpath(".//td[5]//text()")[0].strip()
            web_cite = row.xpath(".//td[8]//text()")[0]
            case = {
                "docket": [docket],
                "name": name,
                "judge": judge,
                "per_curiam": per_curiam,
                "summary": row.xpath(".//td[3]//text()")[0],
                "date": row.xpath(".//td[6]//text()")[0],
                "url": row.xpath(".//a")[0].get("href"),
                "citation": [web_cite],
                "status": "Published",
            }

            if self.court_index == 0:
                citation = ""
                if web_cite not in citation_or_county:
                    citation = citation_or_county
                case["parallel_citation"] = citation
            elif "ohioctapp" in self.court_id:
                case["lower_court"] = f"{citation_or_county} County Court"

            self.cases.append(case)

    from datetime import datetime



    def crawling_range(self, start_date: datetime ,end_date: datetime ) -> int:
        # start_date = datetime(2024,1,1)
        while True:
            if not self.downloader_executed:
                self.html = self._download()

            if (self.max_page_num != -1 and self.page_number > self.max_page_num):
                break

            if(self.page_number == self.max_page_num):
                self._process_html(start_date.year, end_date.year)
                break

            self._process_html(start_date.year, end_date.year)
            self.page_number += 1

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return 0

    def get_court_type(self):
        return "state"

    def get_state_name(self):
         return "Ohio"

    def get_class_name(self):
         return "ohio"

    def get_court_name(self):
         return "Supreme Court of Ohio"
