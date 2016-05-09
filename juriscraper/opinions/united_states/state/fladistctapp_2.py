#  Scraper for Florida 2nd District Court of Appeal
# CourtID: flaapp2
# Court Short Name: flaapp2
# Author: Andrei Chelaru
# Reviewer: mlr
# Log:
# - 2014-07-21: Created
# - 2014-08-28: Updated by mlr.

import re
from datetime import date

import certifi
import requests
from lxml import html
from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        d = date.today()
        self.url = 'http://www.2dca.org/opinions/Opinions_Yearly_Links/{year}/{month_yr}.shtml'.format(
            year=d.year,
            month_yr=d.strftime("%B_%y")
        )

    def _download(self, request_dict={}):
        if self.method == 'LOCAL':
            return super(Site, self)._download(request_dict=request_dict)
        else:
            html_l = super(Site, self)._download(request_dict)
            s = requests.session()
            html_trees = []
            for url in html_l.xpath("//*[@class='cen']/a/@href"):
                logger.info("Getting sub-url: {url}".format(url=url))
                r = s.get(
                    url,
                    headers={'User-Agent': 'Juriscraper'},
                    verify=certifi.where(),
                    **request_dict
                )
                r.raise_for_status()

                # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
                if r.encoding == 'ISO-8859-1':
                    r.encoding = 'cp1252'

                # Grab the content
                text = self._clean_text(r.text)
                html_tree = html.fromstring(text)
                html_tree.make_links_absolute(url)

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
        path = "//th//a[contains(., '/')]/text()"
        return [name for name in html_tree.xpath(path) if name.strip()]

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            download_urls.extend(self._return_download_urls(html_tree))
        return download_urls

    @staticmethod
    def _return_download_urls(html_tree):
        path = "//th//a[contains(., '/')]/@href"
        return list(html_tree.xpath(path))

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            case_dates.extend(self._return_dates(html_tree))
        return case_dates

    @staticmethod
    def _return_dates(html_tree):
        path = "//h1/text()|//h2/text()"
        dates = []
        text = html_tree.xpath(path)[0]
        case_date = convert_date_string(text.strip())
        dates.extend([case_date] * int(html_tree.xpath("count(//th//a[contains(., '/')])")))
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
        path = "//th//a[contains(., '-')]/*/text() | //th//a[contains(text(),'-')]/text()"
        dockets = []
        for text in list(html_tree.xpath(path)):
            text = text.strip()
            if re.match('^\w+-\d+$', text):
                dockets.append(text)
        return dockets

