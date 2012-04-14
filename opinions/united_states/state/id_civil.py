# -*- coding: utf-8 -*-
from GenericSite import GenericSite
from juriscraper.lib.string_utils import clean_string

from datetime import date
from lxml import html
import re
import time


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.isc.idaho.gov/opinions/sccivil.htm'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for xelement in self.html.xpath('//li[@class="MsoNormal"]/span/a[1]'):
            # Our text nodes are randomly surrounded by HTML spans, so we start
            # at a high level node, and strip down to just what we want.
            data_html = html.tostring(xelement, encoding=unicode)
            data_string = re.sub(r'<[^>]*?>', '', data_html)
            data_string = ' '.join(data_string.split())

            # Several regexes are needed since we have hyphen-separated values
            regexes = [u'(.*?)[-–](.*?)–',
                       u'(.*?)[-–](.*)-',
                       u'(.*?)[-–](.*)$']
            for regex in regexes:
                try:
                    case_names.append(re.search(regex, data_string).group(2))
                    # Found what we're looking for...
                    break
                except AttributeError:
                    # Try the next regex...
                    continue

        return case_names

    def _get_download_urls(self):
        download_urls = []
        for e in self.html.xpath('//li[@class="MsoNormal"]/span/a[1]/@href'):
            download_urls.append(e)
        return download_urls

    def _get_case_dates(self):
        dates = []
        for xelement in self.html.xpath('//li[@class="MsoNormal"]/span/a[1]'):
            # Our text nodes are randomly surrounded by HTML spans, so we start
            # at a high level node, and strip down to just what we want.
            data_html = html.tostring(xelement, encoding=unicode)
            data_string = re.sub(r'<[^>]*?>', '', data_html)
            data_string = ' '.join(data_string.split())
            regex = u'(.*?)[-–]'
            try:
                date_string = re.search(regex, data_string).group(1)
            except AttributeError:
                print data_string
            dates.append(date.fromtimestamp(time.mktime(time.strptime(clean_string(date_string), '%B %d, %Y'))))

        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
