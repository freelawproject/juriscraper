"""Scraper for Tenth Circuit of Appeals
CourtID: ca10
Author: mlr
Date created: 6 Sept. 2018
"""
import re

from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'https://www.ca10.uscourts.gov/clerk/oral-argument-recordings'
        self.back_scrape_iterable = [1, 2, 3]
        self._anchor_nodes = None

    def _get_anchor_nodes(self):
        if self._anchor_nodes:
            return self._anchor_nodes

        all_anchors = self.html.xpath('//a')
        mp3_anchors = []
        for anchor in all_anchors:
            hrefs = anchor.xpath('./@href')
            if hrefs and hrefs[0].lower().endswith('.mp3'):
                mp3_anchors.append(anchor)

        # Cache and return it.
        self._anchor_nodes = mp3_anchors
        return mp3_anchors

    def _get_download_urls(self):
        nodes = self._get_anchor_nodes()
        return [node.xpath('./@href')[0] for node in nodes]

    @staticmethod
    def __split_anchor_text(s):
        """Split the anchor text into the docket number and the case name

        Examples: [
            '17-2085, United States v. Roach, Appellant',
            '17-7042 & 17-7044, The Cherokee Nation v. Zinke, et al., Appellants',
            '17-2027, 17-2035, United States v. Solis, Appellant',
        ]

        :return tuple of docket numbers & case name
        """
        # Make the docket number optional. Sometimes it's missing.
        regex = re.compile('(?:(.*\d\d-\d{1,4}), )?(.*)')
        results = regex.search(s)
        docket_number = results.group(1)
        case_name = results.group(2)
        if not docket_number:
            docket_number = "Unknown"
        return docket_number.strip(), case_name.strip()

    def _get_case_names(self):
        nodes = self._get_anchor_nodes()
        case_names = []
        for node in nodes:
            text = node.text_content()
            case_names.append(self.__split_anchor_text(text)[1])
        return case_names

    def _get_docket_numbers(self):
        nodes = self._get_anchor_nodes()
        docket_numbers = []
        for node in nodes:
            text = node.text_content()
            docket_numbers.append(self.__split_anchor_text(text)[0])
        return docket_numbers

    def _get_case_dates(self):
        nodes = self._get_anchor_nodes()
        dates = []
        for node in nodes:
            d_str = node.xpath('./preceding::h3')[0].text_content()
            dates.append(convert_date_string(d_str, fuzzy=True))
        return dates

    def _download_backwards(self, i):
        self.url = 'https://www.ca10.uscourts.gov/clerk/oral-argument-recordings?page=%s' % i
        self.html = self._download()
