# -*- coding: utf-8 -*-
from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import clean_string

from datetime import date
from lxml import html
import re
import time


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.isc.idaho.gov/appeals-court/sccivil'
        self.court_id = self.__module__

    def tweak_request_object(self, r):
        """
        Idaho does not set their encoding properly.
        """
        r.encoding = 'UTF-8'

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//div[@id = "block-system-main"]//li'):
            paths = ['a[1]', 'span/a[1]']
            for path in paths:
                try:
                    e = e.xpath(path)[0]
                    s = html.tostring(e, method='text', encoding='unicode')
                except IndexError:
                    continue
            s = ' '.join(s.split())
            regexes = [u'(.*?) [-–] (.*?)– ',
                       u'(.*?) [-–] (.*)- ',
                       u'(.*?) [-–] (.*)$',
                       u'(.*[0-9]{4})(.*)']
            for regex in regexes:
                try:
                    case_names.append(re.search(regex, s).group(2))
                    # Found what we're looking for...
                    break
                except AttributeError:
                    # Try the next regex...
                    continue
        return case_names

    def _get_download_urls(self):
        download_urls = []
        for e in self.html.xpath('//div[@id = "block-system-main"]//div[contains(concat(" ", @class, " "), " field-items ")]//li/a[1]/@href|'
                                 '//div[@id = "block-system-main"]//div[contains(concat(" ", @class, " "), " field-items ")]//li/span/a[1]/@href'):
            download_urls.append(e)
        return download_urls

    def _get_case_dates(self):
        case_dates = []
        for e in self.html.xpath('//div[@id = "block-system-main"]//div[contains(concat(" ", @class, " "), " field-items ")]//li'):
            s = html.tostring(e, method='text', encoding='unicode')
            s = re.search('(.*[0-9]{4})', s).group(1)
            date_formats = ['%B %d, %Y',
                            '%B %d %Y']
            for format in date_formats:
                try:
                    case_date = date.fromtimestamp(time.mktime(time.strptime(clean_string(s), format)))
                except ValueError:
                    continue
            case_dates.append(case_date)
        return case_dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
