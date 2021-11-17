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
"""

from lxml import html

from juriscraper.lib.html_utils import get_html5_parsed_text
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca2.uscourts.gov/decisions"
        self.method = "POST"
        self.parameters = {
            "IW_SORT": "-DATE",
            "IW_BATCHSIZE": "100",
            "IW_FIELD_TEXT": "*",
            "IW_DATABASE": "Oral Args",
        }
        self.uses_selenium = False
        self.base_xpath = '//tr[contains(.//a/@href, "mp3")]'

    def _make_html_tree(self, text):
        return get_html5_parsed_text(text)

    def _get_download_urls(self):
        path = '//@href[contains(., "mp3")]'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath(f"{self.base_xpath}/td[2]"):
            s = html.tostring(e, method="text", encoding="unicode")
            case_names.append(s)
        return case_names

    def _get_case_dates(self):
        path = f"{self.base_xpath}/td[3]"
        dates = []
        for e in self.html.xpath(path):
            date_string = html.tostring(e, method="text", encoding="unicode")
            # For some reason, some records have mysterious
            # alpha characters after the date, in the date
            # column (example: '9-28-16 B'). Strip it here.
            date_string = date_string.strip().split()[0]
            dates.append(convert_date_string(date_string))
        return dates

    def _get_docket_numbers(self):
        path = f"{self.base_xpath}/td[1]//text()"
        return list(self.html.xpath(path))
