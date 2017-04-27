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

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string, clean_if_py3


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
            html_trees = []
            for url in html_l.xpath("//*[@class='cen']/a/@href"):
                logger.info("Getting sub-url: {url}".format(url=url))
                html_tree = self._get_html_tree_by_url(url, request_dict)
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
        case_names = []
        for name in html_tree.xpath(path):
            name = clean_if_py3(name).strip()
            if name:
                case_names.append(name)
        return case_names

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
        path = "//h1|//h2"
        dates = []
        text = html_tree.xpath(path)[0].text_content().strip()
        case_date = convert_date_string(text)
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
            # sanitize text and extract docket
            text = clean_if_py3(text).split('/')[0].strip()
            docket = ''.join(text.split())
            if re.match(r'^\w+-\d+$', docket):
                dockets.append(docket)
        return dockets

