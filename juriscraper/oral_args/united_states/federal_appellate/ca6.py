"""Oral Argument Audio Scraper for Court of Appeals for the Sixth Circuit
CourtID: ca6
Court Short Name: 6th Cir.
Authors: Brian W. Carver, Michael Lissner
Reviewer: None
History:
  2014-11-06: Started by Brian W. Carver and wrapped up by mlr.
  2016-06-30: Updated by mlr.
"""

import re
from datetime import datetime
from urlparse import urlparse, urljoin, parse_qs

from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.ca6.uscourts.gov/internet/court_audio/aud1.php'
        self.xpath_root = '//table[@class="views-table cols-3"]'
        self.regex = re.compile('((?:\d{2}[- ]\d{4}\s+)+)(.*)')

    def _get_download_urls(self):
        """Two options are currently provided by the site. The first is a link
        to "save" the file, which gives you a zip containing the file. The
        second is a link to "play" the file, which takes you to a flash player.

        The good news is that the link to "play" it contains a real like to
        actually download it inside the 'link' param.
        """
        path_to_flash_page = '//tr/td[2]/a/@href[contains(., "?link=")]'
        links_to_flash = list(self.html.xpath(path_to_flash_page))
        urls = []
        for url in links_to_flash:
            path = parse_qs(urlparse(url).query)['link'][0]
            url = url.replace('www', 'www.opn')  # Uses a different subdomain.
            urls.append(urljoin(url, path))
        return urls

    def _get_case_names(self):
        path = self.xpath_root + '/tr/td[1]/text()'
        case_names = []
        for s in self.html.xpath(path):
            case_names.append(self.regex.search(s).group(2))
        return case_names

    def _get_case_dates(self):
        dates = []
        # Multiple items are listed under a single date.
        date_path = './/th[1]'
        # For every table full of OA's...
        for table in self.html.xpath(self.xpath_root):
            # Find the date str, e.g. "10-10-2014 - Friday"
            date_str = table.xpath(date_path)[0].text_content()
            d = datetime.strptime(date_str[:10], '%m-%d-%Y').date()

            # The count of OAs on a date is the number of rows minus the header
            # row.
            total_rows = len(table.xpath('.//tr')) - 1
            dates.extend([d] * total_rows)
        return dates

    def _get_docket_numbers(self):
        path = self.xpath_root + '/tr/td[1]/text()'
        return [self.regex.search(s).group(1).strip().replace(' ', '-') for
                s in self.html.xpath(path)]
