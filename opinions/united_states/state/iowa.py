#  Scraper for Iowa Supreme Court
# CourtID: iowa
# Court Short Name: iowa
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 25 July 2014


from datetime import date
import time

import certifi
from lxml import html
import requests
import re
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().year
        self.url = 'http://www.iowacourts.gov/About_the_Courts/Supreme_Court/Supreme_Court_Opinions/Opinions_Archive/index.asp'

    def _download(self, request_dict={}):
        if self.method == 'LOCAL':
            # Note that this is returning a list of HTML trees.
            html_trees = [super(Site, self)._download(request_dict=request_dict)]
        else:
            html_l = OpinionSite._download(self)
            s = requests.session()
            html_trees = []
            for url in html_l.xpath("//td[@width='49%']//tr[contains(., ', {year}')]/td[5]/a/@href".format(year=self.year)):
                r = s.get(
                    url,
                    headers={'User-Agent': 'Juriscraper'},
                    verify=certifi.where(),
                    **request_dict
                )
                r.raise_for_status()

                # If the encoding is iso-8859-1, switch it to cp1252 (a
                # superset)
                if r.encoding == 'ISO-8859-1':
                    r.encoding = 'cp1252'

                # Grab the content
                text = self._clean_text(r.text)
                html_tree = html.fromstring(text)
                html_tree.make_links_absolute(self.url)

                remove_anchors = lambda url: url.split('#')[0]
                html_tree.rewrite_links(remove_anchors)
                html_trees.append(html_tree)
        return html_trees

    def _get_case_names(self):
        case_names = []
        for html_tree in self.html:
            case_names.extend(self._return_case_names(html_tree))
        return case_names

    @staticmethod
    def _return_case_names(html_tree):
        path = "//*[contains(concat(' ',@id,' '),' wfLabel')]/text()"
        return [titlecase(s.strip().lower()) for s in html_tree.xpath(path)]

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            download_urls.extend(self._return_download_urls(html_tree))
        return download_urls

    @staticmethod
    def _return_download_urls(html_tree):
        path = "//*[contains(concat(' ',@id,' '),' wfLabel')]/preceding::tr[2]/td[1]/a/@href"
        return list(html_tree.xpath(path))

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            case_dates.extend(self._return_dates(html_tree))
        return case_dates

    @staticmethod
    def _return_dates(html_tree):
        path = "//*[contains(concat(' ',@id,' '),' wfHeader') and not(contains(., 'Iowa'))]/text()"
        dates = []
        text = html_tree.xpath(path)[0]
        case_date = date.fromtimestamp(time.mktime(time.strptime(text.strip(), '%B %d, %Y')))
        dates.extend([case_date] * int(html_tree.xpath("count(//*[contains(concat(' ',@id,' '),' wfLabel')])")))
        return dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree in self.html:
            docket_numbers.extend(self._return_docket_numbers(html_tree))
        return docket_numbers

    @staticmethod
    def _return_docket_numbers(html_tree):
        path = "//*[contains(concat(' ',@id,' '),' wfLabel')]/preceding::tr[2]/td[1]/a/text()"
        return [re.sub('Nos?.', '', e).strip() for e in html_tree.xpath(path)]
