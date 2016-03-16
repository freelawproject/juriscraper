"""Scraper for Kentucky Supreme Court
CourtID: ky
Court Short Name: Ky.

History:
    2014-08-07: Created by mlr.
    2014-12-15: Updated to fetch 100 results instead of 30. For reasons unknown
                this returns more recent results, while a smaller value leaves
                out some of the most recent items.
Notes:
    This scraper is unique. Kentucky does not provide case names in the search
    results pages, making them almost useless. They have a separate interface
    though that allows a lookup by case year and number, which *does* provide
    the case name (and lots of other information). Note that it only provides
    this information for supreme court cases, so extending this to do kyctapp
    won't be possible.

    Our process is therefore:
      1. Get anything we can from the search results.
      1. For extra meta data, query system number two and get back the case
         name.
      1. Merge it all.

    Also fun, they use IP addresses instead of DNS and hide them behind HTML
    frames hosted by real domains.

    I tried calling to get more information, and though they've heard of us (a
    first!), they didn't want to help, and seemed downright aggressive in their
    opposition. Curious. Anyway, don't bother calling  again.

    You can contact support@dtsearch.com with questions about the search
    interface. Best of luck.
"""
from datetime import datetime

import certifi

import re
import requests
from lxml import html
from requests.exceptions import HTTPError, ConnectionError, Timeout
from juriscraper.AbstractSite import logger
from juriscraper.DeferringList import DeferringList
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
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
            'maxFiles': '100',
            # This is a dtSearch trick that brings back all results.
            'request': 'xfirstword',
            # This provides things in newest-first order, but indeed shows the
            # most recent N items.
            'sort': 'Date'
        }
        self.method = 'POST'
        self.docket_number_regex = re.compile('(?P<year>\d{4})-(?P<court>[SC]{2})-(?P<docket_num>\d+)')
        self.hrefs_contain = 'Opinions'

    def _get_download_urls(self):
        path = "//a[@href[contains(., '{m}')]]".format(m=self.hrefs_contain)
        elems = filter(self._has_valid_docket_number, self.html.xpath(path))
        return [e.xpath('./@href')[0] for e in elems]

    def _get_case_names(self):
        def fetcher(elem):
            """This reaches out to a secondary system and scrapes the correct
             info.

            You can find the front end of this system here:
              - http://162.114.92.78/dockets/SearchbyCaseNumber.htm and
              - http://162.114.92.78/dockets/
            """
            if self.method == 'LOCAL':
                return "No case names fetched during tests."
            else:
                ip_addresses = ['162.114.92.72', '162.114.92.78']
                for ip_address in ip_addresses:
                    last_item = (ip_addresses.index(ip_address) == len(ip_addresses) - 1)
                    url = 'http://%s/dockets/SearchCaseDetail.asp' % ip_address
                    anchor_text = html.tostring(elem, method='text', encoding='unicode')
                    m = self.docket_number_regex.search(anchor_text)

                    try:
                        r = requests.post(
                            url,
                            headers={'User-Agent': 'Juriscraper'},
                            timeout=5,
                            verify=certifi.where(),
                            data={
                                'txtyear': m.group('year'),
                                'txtcasenumber': m.group('docket_num').strip('0'),
                                'cmdnamesearh': 'Search',
                            },
                        )

                        # Throw an error if a bad status code is returned,
                        # otherwise, break the loop so we don't try more ip
                        # addresses than necessary.
                        r.raise_for_status()
                        break
                    except HTTPError, e:
                        logger.info("404 error connecting to: {ip}".format(
                            ip=ip_address,
                        ))
                        if e.response.status_code == 404 and not last_item:
                            continue
                        else:
                            raise e
                    except (ConnectionError, Timeout), e:
                        logger.info("Timeout/Connection error connecting to: {ip}".format(
                            ip=ip_address,
                        ))
                        if not last_item:
                            continue
                        else:
                            raise e

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
                        case_name_parts.append(titlecase(s.strip().lower()))
                    if len(case_name_parts) == 2:
                        break
                return ' v. '.join(case_name_parts)

        # Get the docket numbers to use for queries.
        path = "//a[@href[contains(., '{m}')]]".format(m=self.hrefs_contain)
        elements = filter(self._has_valid_docket_number, self.html.xpath(path))
        return DeferringList(seed=elements, fetcher=fetcher)

    def _get_docket_numbers(self):
        path = "//a[@href[contains(., '{m}')]]".format(
            m=self.hrefs_contain)
        elements = filter(self._has_valid_docket_number, self.html.xpath(path))
        return map(self._return_docket_number_from_str, elements)

    def _has_valid_docket_number(self, e):
        text = html.tostring(e, method='text', encoding='unicode')
        if self.docket_number_regex.search(text):
            return True
        else:
            return False

    def _return_docket_number_from_str(self, e):
        s = html.tostring(e, method='text', encoding='unicode')
        m = self.docket_number_regex.search(s)
        return '{year} {court} {docket_num}'.format(
            year=m.group('year'),
            court=m.group('court'),
            docket_num=m.group('docket_num')
        )

    def _get_case_dates(self):
        path = "//tr[descendant::a[@href[contains(., '{m}')]]]/td[2]".format(
            m=self.hrefs_contain)
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
        return ['Unknown'] * len(self.case_names)
