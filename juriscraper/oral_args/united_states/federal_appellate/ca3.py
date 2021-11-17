#  Scraper for Third Circuit of Appeals
# CourtID: ca3
# Court Short Name: ca3
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 18 July 2014

import re
from datetime import datetime

from juriscraper.lib.string_utils import fix_camel_case
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "http://www2.ca3.uscourts.gov/oralargument/OralArguments.xml"
        )
        self.regex = r"(\d{2}-\d{3,4})?(.+)\.(:?(wma)|(mp3)|(m4a))"

    def _get_download_urls(self):
        path = "//item/link"
        return list(map(self._return_download_url, self.html.xpath(path)))

    @staticmethod
    def _return_download_url(e):
        return f"http://www2.ca3.uscourts.gov{e.tail}"

    def _get_case_names(self):
        path = "//item/title/text()"
        case_names = []
        for s in self.html.xpath(path):
            case_name = re.search(self.regex, s).group(2)
            case_names.append(fix_camel_case(case_name))
        return case_names

    def _get_case_dates(self):
        path = "//item/description/text()"
        return list(map(self._return_case_date, self.html.xpath(path)))

    @staticmethod
    def _return_case_date(e):
        return datetime.strptime(e, "%m/%d/%Y").date()

    def _get_docket_numbers(self):
        path = "//item/title/text()"
        return list(map(self._return_docket_number, self.html.xpath(path)))

    def _return_docket_number(self, e):
        case_name = re.search(self.regex, e)
        docket_number = case_name.group(1)
        if docket_number:
            # Surround ampersands with spaces and remove dup spaces if created
            docket_number = " ".join(re.sub("&", " & ", docket_number).split())
            return docket_number
        else:
            return ""
