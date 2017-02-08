"""Scraper for First Circuit of Appeals
CourtID: ca1
Court Short Name: ca1
Author: Michael Lissner
Date created: 13 June 2014
"""

from datetime import datetime
import re

from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.string_utils import clean_if_py3


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://media.ca1.uscourts.gov/files/audio/audiorss.php'

    def _get_download_urls(self):
        # For some reason, lxml is being weird while parsing this XML and is
        # munging the link node into a text node. This xpath seems to work
        # despite it being rather wonky.
        path = '//item/link'
        download_urls = []
        for t in self.html.xpath(path):
            download_urls.append(t.tail)
        return download_urls

    def _get_case_names(self):
        case_names = []
        for t in self.html.xpath('//item/title/text()'):
            case_name = t.split(', ', 1)[1]
            case_names.append(case_name)
        return case_names

    def _get_case_dates(self):
        path = '//item/description/b/text()'
        dates = []
        for t in self.html.xpath(path):
            # t looks like: [Argued:91-1-2015]
            t = re.sub(r'[\[\]\s]', '', t)             # Strip out [ and ].
            date_string = clean_if_py3(t).split(':', 1)[1].strip()  # Then get the date part.
            dates.append(datetime.strptime(date_string, '%m-%d-%Y').date())
        return dates

    def _get_docket_numbers(self):
        document_numbers = []
        for t in self.html.xpath('//item/title/text()'):
            case_name = t.split(', ', 1)[0]
            case_name = re.sub(r'case:\s?', '', case_name, re.I)
            document_numbers.append(case_name)
        return document_numbers
