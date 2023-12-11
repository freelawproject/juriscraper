"""Scraper for Second Circuit
CourtID: ca2
Author: MLR
Reviewer: MLR
Contact:
  Webmaster@ca2.uscourts.gov ('Calendar Team' handles updates, and is responsive)
  ecfhelpdesk@ca2.uscourts.gov
  Shane_Clouden@ca2.uscourts.gov
History:
  2016-09-09: Created by MLR
  2023-11-21: Fixed by flooie
  2023-12-11: Fixed by quevon24
"""
from datetime import date, timedelta

from dateutil.rrule import DAILY, rrule
from lxml import html

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear


class Site(OralArgumentSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interval = 30
        self.court_id = self.__module__
        self.url = "https://ww3.ca2.uscourts.gov/decisions"
        self.method = "POST"
        self.base_xpath = '//tr[contains(.//a/@href, "mp3")]'
        self.parameters = {
            "IW_SORT": "-DATE",
            "IW_BATCHSIZE": "50",
            "IW_FILTER_DATE_BEFORE": "",
            "IW_FILTER_DATE_AFTER": "NaNNaNNaN",
            "IW_FIELD_TEXT": "*",
            "IW_DATABASE": "Oral Args",
            "opinion": "*",
        }
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                interval=self.interval,
                dtstart=date(2023, 6, 14),
                until=date(2023, 12, 11),
            )
        ]

    def _process_html(self):
        self._extract_cases_from_html(self.html)

    def _download(self, request_dict={}):
        if self.test_mode_enabled():
            self.html = super()._download()
            return self.html
        r = self.request["session"].post(self.url, params=self.parameters)
        return html.fromstring(r.content)

    def _extract_cases_from_html(self, html):
        for row in html.xpath("//table[@border='1']"):
            link = row.xpath(".//a")[0].get("href")
            docket = (
                row.xpath(".//a/nobr/text()")[0]
                if row.xpath(".//a/nobr/text()")
                else None
            )
            if row.xpath(".//td/text()"):
                name, date = row.xpath(".//td/text()")
            else:
                continue
            if docket and link and name and date:
                # empty row in date ranges between 10-12-2023 and 11-11-2023
                self.cases.append(
                    {"docket": docket, "url": link, "name": name, "date": date}
                )

    def extract_next_page_url(self, html):
        """Return the href url from "Next" pagination element
        if it exists, otherwise return False.
        """
        path = '//table//tr/td[2]/font/a[contains(., "Next")]/@href'
        elements = html.xpath(path)
        return (
            f"https://ww3.ca2.uscourts.gov{elements[0]}" if elements else False
        )

    def _get_case_dates(self):
        dates = []
        for case in self.cases:
            if case["date"] == "22-2649":
                # Incorrect data in column range between 06-14-2023 and 06-30-2023
                case["date"] = "6-14-23"
                case["docket"] = "22-2649"
            dates.append(convert_date_string(case["date"]))
        return dates

    def _download_backwards(self, d):
        # Date format: %Y%m%d = 20231111
        self.parameters.update(
            {
                "IW_FILTER_DATE_BEFORE": (
                    d + timedelta(self.interval)
                ).strftime("%Y%m%d"),
                "IW_FILTER_DATE_AFTER": d.strftime("%Y%m%d"),
            }
        )
        self.html = self._download()

        proceed = True
        while proceed:
            next_page_url = self.extract_next_page_url(self.html)
            if next_page_url:
                self.html = self._get_html_tree_by_url(next_page_url)
                self._extract_cases_from_html(self.html)
            else:
                proceed = False

        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
