"""Scraper for Kentucky Supreme Court
CourtID: ky
Court Short Name: Ky.

History:
    2014-08-07: Created by mlr.
    2014-12-15: Updated to fetch 100 results instead of 30. For reasons unknown
                this returns more recent results, while a smaller value leaves
                out some of the most recent items.
    2016-03-16: Restructured by arderyp to pre-process all data at donwload time
                to work around resources whose case names cannot be fetched to
                to access restrictions.
Notes:
    This scraper is unique. Kentucky does not provide case names in the primary
    search portal's result page, making them almost useless. They have a secondary
    search portal that allows a lookup by case year and number, which *does* provide
    the case name (and lots of other information). Note that it only provides
    this information for supreme court cases, so extending this to do kyctapp
    won't be possible.

    Primary Search Portal:      http://162.114.92.72/dtsearch.asp
    Secondary Search Portal:    http://162.114.92.78/dockets/SearchbyCaseNumber.htm

    Our two step process is as follows:
      1. Get the pdf url, case date, and docket number from the Primary Search Portal
      2. If the above data is valid, use publication year and docket number
         to fetch case name from Secondary Search Portal

    Unlike other scrapers, all of the metadata above is gathered at download time,
    saved on the local object, and merely echoed back in by the standard getters.
    This design allows us to avoid issues with cases that have restricted access
    in the Secondary Search Portal (example: year=2015, docket=000574).  These
    restricted resources will be skipped.

    Also fun, they use IP addresses instead of DNS and hide them behind HTML
    frames hosted by real domains.

    I tried calling to get more information, and though they've heard of us (a
    first!), they didn't want to help, and seemed downright aggressive in their
    opposition. Curious. Anyway, don't bother calling  again.

    You can contact support@dtsearch.com with questions about the search
    interface. Best of luck.
"""

import re
import certifi
import requests
from lxml import html
from requests.exceptions import HTTPError, ConnectionError, Timeout

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    CASE_NAMES = []
    CASE_DATES = []
    DOWNLOAD_URLS = []
    DOCKET_NUMBERS = []

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
            'maxFiles': '100',              # Fetch 100 results
            'request': 'xfirstword',        # dtSearch trick to return all results
            'sort': 'Date'                  # Order by newest first
        }
        self.method = 'POST'
        self.docket_number_regex = re.compile(r'(?P<year>\d{4})-(?P<court>[SC]{2})-(?P<number>\d+)')
        self.hrefs_contain = 'Opinions'

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        self._build_data_lists_from_html(html)
        return html

    def _build_data_lists_from_html(self, html):
        # Search second column cells for valid opinions
        data_cell_path = '//table/tr/td[2]/font'
        for cell in html.xpath(data_cell_path):
            # Cell must contain a link
            if cell.xpath('a'):
                link_href = cell.xpath('a/@href')[0].strip()
                link_text = cell.xpath('a/text()')[0].strip()
                cell_text = cell.xpath('text()')
                date = self._parse_date_from_cell_text(cell_text)
                # Cell must contain a parse-able date
                if date:
                    docket_match = self.docket_number_regex.search(link_text)
                    # Cell must contain a docket number conforming to expected format
                    if docket_match:
                        if self.method == 'LOCAL':
                            # Don't fetch names when running tests
                            name = 'No case names fetched during tests.'
                        else:
                            # Fetch case name from external portal search (see doc string at top for details)
                            name = self._fetch_case_name(docket_match.group('year'), docket_match.group('number'))
                        if name:
                            docket_number = '%s %s %s' % (
                                docket_match.group('year'),
                                docket_match.group('court'),
                                docket_match.group('number'),
                            )
                            self.CASE_NAMES.append(name)
                            self.CASE_DATES.append(date)
                            self.DOCKET_NUMBERS.append(docket_number)
                            self.DOWNLOAD_URLS.append(link_href)

    def _parse_date_from_cell_text(self, cell_text):
        date = False
        for text in cell_text:
            try:
                date = convert_date_string(text.strip())
                break
            except ValueError:
                pass
        return date

    def _fetch_case_name(self, year, number):
        """Fetch case name for a given docket number + publication year pair.

        Some resources show 'Public Access Restricted' messages and do not
        provide parseable case name information.  These will be skipped by
        our system by returning False below.  The only other approach would
        be to parse the case name from the raw PDF text itself.
        """

        ip_addresses = ['162.114.92.72', '162.114.92.78']
        for ip_address in ip_addresses:
            last_ip = (ip_address == ip_addresses[-1])
            url = 'http://%s/dockets/SearchCaseDetail.asp' % ip_address

            try:
                r = requests.post(
                    url,
                    headers={'User-Agent': 'Juriscraper'},
                    timeout=60,
                    verify=certifi.where(),
                    data={
                        'txtyear': year,
                        'txtcasenumber': number,
                        'cmdnamesearh': 'Search',
                    },
                )

                # Throw an error if a bad status code is returned,
                # otherwise, break the loop so we don't try more ip
                # addresses than necessary.
                r.raise_for_status()
                break
            except HTTPError as e:
                logger.info('404 error connecting to: %s' % ip_address)
                if e.response.status_code == 404 and not last_ip:
                    continue
                else:
                    raise e
            except (ConnectionError, Timeout) as e:
                logger.info('Timeout/Connection error connecting to: %s' % ip_address)
                if not last_ip:
                    continue
                else:
                    raise e

        # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
        if r.encoding == 'ISO-8859-1':
            r.encoding = 'cp1252'

        # Grab the content
        page_text = self._clean_text(r.text)
        html_tree = html.fromstring(page_text)

        # And finally, we parse out the good stuff.
        parties_path = "//tr[descendant::text()[contains(., 'Appell')]]//td[3]//text()"
        case_name_parts = []
        for text in html_tree.xpath(parties_path):
            text = text.strip()
            if text:
                case_name_parts.append(titlecase(text.lower()))
            if len(case_name_parts) == 2:
                break
        if case_name_parts:
            return ' v. '.join(case_name_parts)
        else:
            return False

    def _get_download_urls(self):
        return self.DOWNLOAD_URLS

    def _get_case_names(self):
        return self.CASE_NAMES

    def _get_docket_numbers(self):
        return self.DOCKET_NUMBERS

    def _get_case_dates(self):
        return self.CASE_DATES

    def _get_precedential_statuses(self):
        return ['Unknown'] * len(self.CASE_NAMES)
