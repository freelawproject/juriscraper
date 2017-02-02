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
from six.moves.urllib.parse import urlparse, urljoin, parse_qs

from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.ca6.uscourts.gov/internet/court_audio/aud1.php'
        self.xpath_root = '//table[@class="views-table cols-3"]'
        self.regex = re.compile('((?:\d{2}[- ]\d{4}\s*)+)(.*)')
        self.back_scrape_iterable = ['nothing']  # Just a placeholder for this court
        self.backscrape = False

    def _get_download_urls(self):
        """Two options are currently provided by the site. The first is a link
        to "save" the file, which gives you a zip containing the file. The
        second is a link to "play" the file, which takes you to a flash player.

        The good news is that the link to "play" it contains a real link to
        actually download it inside the 'link' param.
        """
        if self.backscrape:
            path_to_flash_page = '//tr/td[3]/a/@href[contains(., "?link=")]'
        else:
            path_to_flash_page = '//tr/td[2]/a/@href[contains(., "?link=")]'
        links_to_flash = list(self.html.xpath(path_to_flash_page))
        urls = []
        for url in links_to_flash:
            path = parse_qs(urlparse(url).query)['link'][0]
            # Remove newlines and line returns from urls.
            path = path.replace('\n', '').replace('\r', '')

            if 'www.opn' not in url:
                # Update the URL if it's not the one we want.
                url = url.replace('www', 'www.opn')
            urls.append(urljoin(url, path))
        return urls

    def _get_case_names(self):
        if self.backscrape:
            path = self.xpath_root + '//td[2]/text()'
        else:
            path = self.xpath_root + '/tr/td[1]/text()'
        case_names = []
        for s in self.html.xpath(path):
            case_names.append(self.regex.search(s).group(2))
        return case_names

    def _get_case_dates(self):
        dates = []
        if self.backscrape:
            date_strs = self.html.xpath('//table//td[1]//text()')
            return [convert_date_string(s) for s in date_strs]
        else:
            # Multiple items are listed under a single date.
            date_path = './/th[1]'
            # For every table full of OA's...
            for table in self.html.xpath(self.xpath_root):
                # Find the date str, e.g. "10-10-2014 - Friday"
                date_str = table.xpath(date_path)[0].text_content()
                d = datetime.strptime(date_str[:10], '%m-%d-%Y').date()

                # The count of OAs on a date is the number of rows minus the
                # header row.
                total_rows = len(table.xpath('.//tr')) - 1
                dates.extend([d] * total_rows)
            return dates

    def _get_docket_numbers(self):
        if self.backscrape:
            path = self.xpath_root + '//td[2]/text()'
        else:
            path = self.xpath_root + '/tr/td[1]/text()'
        return [self.regex.search(s).group(1).strip().replace(' ', '-') for
                s in self.html.xpath(path)]

    def _download_backwards(self, _):
        """You can get everything with a single POST, thus we just ignore the
        back_scrape_iterable.
        """
        self.backscrape = True
        self.method = 'POST'
        self.xpath_root = '//table'
        self.url = 'http://www.opn.ca6.uscourts.gov/internet/court_audio/audSearchRes.php'
        self.parameters = {
            'caseNumber': "",
            'shortTitle': "",
            'dateFrom': '01/01/2013',
            'dateTo': '01/01/2015',
            'Submit': 'Submit+Query',
        }
        self.html = self._download()
