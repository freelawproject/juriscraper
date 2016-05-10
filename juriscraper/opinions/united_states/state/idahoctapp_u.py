# coding=utf-8
import time
import re
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import clean_string
from lxml import html
from datetime import date


class Site(OpinionSite):
    """Unfortunately, while Idaho has updated all of its other pages to use nice
    tables, ctapp_u continues to use a nasty ul. This scraper used to live
    almost char for char in idaho_civil, before it was updated. Alas, now it
    lives here.
    """
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.isc.idaho.gov/appeals-court/coaunpublished'
        self.base_path = '//div[@id = "block-system-main"]//div[contains(concat(" ", @class, " "), " field-items ")]//li'
        self.sub_paths = [
            'a[./text()][1]',
            'span/a[./text()][1]',
            'span/span/a[./text()][1]'
        ]
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.case_names)

    def tweak_request_object(self, r):
        """
        Idaho does not set their encoding properly.
        """
        r.encoding = 'UTF-8'

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath(self.base_path):
            for path in self.sub_paths:
                try:
                    sub_e = e.xpath(path)[0]
                    s = html.tostring(sub_e, method='text', encoding='unicode')
                    break
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
        for e in self.html.xpath(self.base_path):
            for path in self.sub_paths:
                try:
                    sub_e = e.xpath('%s/@href' % path)[0]
                except IndexError:
                    continue
            download_urls.append(sub_e)
        return download_urls

    def _get_case_dates(self):
        case_dates = []
        for e in self.html.xpath(self.base_path):
            s = html.tostring(e, method='text', encoding='unicode')
            s = re.search('(.*[0-9]{4})', s).group(1)
            date_formats = ['%B %d, %Y',
                            '%B %d %Y']
            for format in date_formats:
                try:
                    case_date = date.fromtimestamp(
                        time.mktime(time.strptime(clean_string(s), format)))
                except ValueError:
                    continue
            case_dates.append(case_date)
        return case_dates
