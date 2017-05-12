# -*- coding: utf-8 -*-
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import clean_string

from datetime import date
from lxml import html
import re
import time


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.isc.idaho.gov/opinions/cacivil.htm'
        self.court_id = self.__module__

    def tweak_response_object(self):
        """
        This state uses an HTTP header to indicate an encoding of UTF-8,
        but the encoding is actually ISO-8859-1, as indicated in the HTML
        itself. When this page is rendered in Firefox, chardet fails, and
        many unknown characters are displayed to the user. Setting the
        character encoding manually fixes the issue.
        """
        self.request['response'].encoding = 'ISO-8859-1'

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
        case_dates = []
        for e in self.html.xpath('//li[@class="MsoNormal"]/span/a[1]'):
            s = html.tostring(e, method='text', encoding='unicode')
            # Cleanup...
            s = s.split(u'-')[0]
            s = s.split(u'–')[0]
            date_formats = ['%B %d, %Y',
                            '%B %d %Y',
                            '%B %d , %Y']
            for format in date_formats:
                try:
                    case_date = date.fromtimestamp(time.mktime(time.strptime(clean_string(s), format)))
                except ValueError:
                    continue
            case_dates.append(case_date)
        return case_dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
