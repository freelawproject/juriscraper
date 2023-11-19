"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
Contact: Email "Internet and Technology" staff listed at http://www.cobar.org/staff
         they usually fix issues without responding to the emails directly. You can
         also try submitting the form here: http://www.cobar.org/contact
History:
    - 2022-01-31: Updated by William E. Palin
    - 2023-01-05: Updated by WEP
    - 2023-11-19: Drop Selenium by WEP
"""
import datetime
import re
from datetime import date, timedelta

from dateutil import parser

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.six_months_ago = date.today() - timedelta(180)
        self.status = "Published"
        self.url = f"https://www.courts.state.co.us/Courts/Supreme_Court/Proceedings/Index.cfm"

    def match_regex(self, str):
        """Match date regex patterns

        :param str: Date Str
        :return: Date object or none
        """
        date_match = re.search(
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b",
            str,
        )
        if date_match:
            return parser.parse(date_match.group(0)).date()
        return None

    def extract_dates(self, row, partial_date):
        """Extract out one of the many date patterns

        :param row: Row to process
        :param partial_date: Partial date string
        :return: Date object and approximate boolean
        """
        raw_dates = row.xpath(
            "following-sibling::div/p/a/following-sibling::text()"
        )
        raw_date_str = " ".join(raw_dates)
        date = self.match_regex(raw_date_str)
        if date:
            return date, False
        raw_date_str = row.xpath("following-sibling::div/p/a/text()")[0]
        date = self.match_regex(raw_date_str)
        if date:
            return date, False
        date_object = datetime.datetime.strptime(partial_date, "%b %Y").date()
        return date_object, True

    def _process_html(self):
        for row in self.html.xpath("//div[@id='Dispositions']/*"):
            if row.tag == "a":
                docket, name = (
                    row.xpath("following-sibling::text()")[0]
                    .strip()
                    .split(" ", 1)
                )
                if "\xa0\xa0" not in name:
                    continue
                name, partial_date = name.split("\xa0\xa0")
                url = row.xpath("following-sibling::div/p/a/@href")[-1]
                date, date_filed_is_approximate = self.extract_dates(
                    row, partial_date
                )
                if date < self.six_months_ago:
                    continue
                self.cases.append(
                    {
                        "date": str(date),
                        "name": name,
                        "docket": docket,
                        "url": url,
                        "date_filed_is_approximate": date_filed_is_approximate,
                    }
                )
