"""Scraper for Kentucky Supreme Court
CourtID: ky
Court Short Name: Ky.
Author: mlr
Reviewer: None
Date created: 2014-08-07

This scraper is unique. Kentucky does not provide case names in the search
results pages, making them almost useless. They have a separate interaface
though that allows a lookup by case year and number, which *does* provide the
case name.

Our process is therefore:
1. Get anything we can from the search results.
2. For extra meta data, query system number two and get back the case name.
3. Merge it all.

Also fun, they use IP addresses instead of DNS and hide them behind HTML
frames.

One of the worst ones. I tried calling to get more information, and though
they've heard of us (a first!), they didn't want to help, and seemed downright
aggressive in their opposition. Curious. Anyway, don't bother calling  again.
"""

import re
import requests
from datetime import datetime
from lxml import html

from juriscraper.lib.string_utils import titlecase
from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://162.114.92.72/dtsearch.asp'
        self.parameters = {
            'SearchForm': '%%SearchForm%%',
            'autoStopLimit': '0',
            'cmd': 'search',
            'fuzziness': '0',
            'index': 'D:\\Inetpub\\wwwroot\\indices\\SupremeCourt_Index',
            # This can be bumped as high as you dream to get back *massive*
            # result sets.
            'maxFiles': '10',
            # This is a dtSearch trick that brings back all results.
            'request': 'xfirstword',
            # This provides things in newest-first order, but indeed shows the
            # most recent N items.
            'sort': 'Date'
        }
        self.method = 'POST'
        self.docket_number_regex = re.compile('(?P<year>\d{4})-(?P<court>[CAS]{2})-(?P<docket_num>\d+)')

    def _get_download_urls(self):
        path = "//a[@href[contains(., 'Opinions')]]"
        elems = filter(self._has_valid_docket_number, self.html.xpath(path))
        return [e.xpath('./@href')[0] for e in elems]

    def _get_case_names(self):
        """This reaches out to a secondary system and scrapes the correct info.
        """
        url = 'http://162.114.92.78/dockets/SearchCaseDetail.asp'

        def fetcher(e):
            text = html.tostring(e, method='text', encoding='unicode')
            m = self.docket_number_regex.search(text)

            r = requests.post(
                url,
                headers={'User-Agent': 'Juriscraper'},
                data={
                    'txtyear': m.group('year'),
                    'txtcasenumber': m.group('docket_num').strip('0'),
                    'cmdnamesearh': 'Search',
                },
            )

            # Throw an error if a bad status code is returned.
            r.raise_for_status()

            # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
            if r.encoding == 'ISO-8859-1':
                r.encoding = 'cp1252'

            # Grab the content
            text = self._clean_text(r.text)
            html_tree = html.fromstring(text)

            # And finally, we parse out the good stuff.
            parties_path = "//tr[descendant::text()[contains(., 'Appell')]]//td[3]//text()"
            case_name_parts = []
            for s in html_tree.xpath(parties_path):
                if s.strip():
                    case_name_parts.append(titlecase(s.strip()))
                if len(case_name_parts) == 2:
                    break
            return ' v. '.join(case_name_parts)

        # Get the docket numbers to use for queries.
        path = "//a[@href[contains(., 'Opinions')]]"
        elements = filter(self._has_valid_docket_number, self.html.xpath(path))
        return DeferringList(seed=elements, fetcher=fetcher)

    def _get_docket_numbers(self):
        path = "//a[@href[contains(., 'Opinions')]]"
        elements = filter(self._has_valid_docket_number, self.html.xpath(path))
        return map(self._return_docket_number_from_str, elements)

    def _return_docket_number_from_str(self, e):
        s = html.tostring(e, method='text', encoding='unicode')
        m = self.docket_number_regex.search(s)
        return '{year} {court} {docket_num}'.format(
            year=m.group('year'),
            court=m.group('court'),
            docket_num=m.group('docket_num')
        )

    def _get_case_dates(self):
        path = "//tr[descendant::a[@href[contains(., 'Opinions')]]]/td[2]"
        elements = filter(self._has_valid_docket_number, self.html.xpath(path))
        dates = []
        for e in elements:
            for s in e.xpath('.//text()'):
                s = s.strip()
                try:
                    dates.append(datetime.strptime(s, '%m/%d/%Y').date())
                except ValueError:
                    pass
        return dates

    def _get_precedential_statuses(self):
        # noinspection PyUnresolvedReferences
        return ['Published'] * len(self.case_names)

    def _has_valid_docket_number(self, e):
        text = html.tostring(e, method='text', encoding='unicode')
        if self.docket_number_regex.search(text):
            return True
        else:
            return False

    '''
    def _get_neutral_citations(self):
        """
          This is often of the form year, state abbreviation, sequential number
          as in '2013 Neb. 12' which would be the 12th opinion issued in 2013.
        """
        return None
    '''
