#  Scraper for Kansas Supreme Court
# CourtID: kan
# Court Short Name: kan
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 25 July 2014


from datetime import date
import time

import certifi
import re
from lxml import etree, html
import requests
from juriscraper.OpinionSite import OpinionSite
from juriscraper.AbstractSite import logger


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_index = 1
        self.date = date.today()
        self.url = 'http://www.kscourts.org/Cases-and-Opinions/Date-of-Release-List/'

    def _download(self, request_dict={}):
        if self.method == 'LOCAL':
            # Note that this is returning a list of HTML trees.
            html_trees = [super(Site, self)._download(request_dict=request_dict)]
        else:
            html_l = OpinionSite._download(self)
            s = requests.session()
            html_trees = []
            # The latest 5 urls on the page.
            path = "//td[@width='50%'][{court_index}]/h3[contains(., '{year}')]/following::ul[1]//a/@href".format(
                court_index=self.court_index,
                year=self.date.year,
            )
            for url in html_l.xpath(path)[0:4]:
                logger.info("Downloading Kansas page at: {url}".format(url=url))
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
            try:
                parent_elem = html_tree.xpath("//p/font[a]")[0]
            except IndexError:
                # When there were no opinions that week.
                continue
            etree.strip_tags(parent_elem, 'em')
            case_names.extend(self._return_case_names(parent_elem))
        return case_names

    @staticmethod
    def _return_case_names(parent_elem):
        path = "./a[contains(./@href, '.pdf')]"
        return [e.tail.strip() for e in parent_elem.xpath(path)]

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            download_urls.extend(self._return_download_urls(html_tree))
        return download_urls

    @staticmethod
    def _return_download_urls(html_tree):
        path = "//a[contains(./@href, '.pdf')]/@href"
        return list(html_tree.xpath(path))

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            case_dates.extend(self._return_dates(html_tree))
        return case_dates

    @staticmethod
    def _return_dates(html_tree):
        path = "//*[starts-with(., 'Kansas')][contains(., 'Released')]/text()[2]"
        text = html_tree.xpath(path)[0]
        text = re.sub('Opinions Released', '', text)
        for date_format in ('%B %d, %Y', '%B %d. %Y'):
            try:
                case_date = date.fromtimestamp(
                    time.mktime(time.strptime(text.strip(), date_format)))
            except ValueError:
                continue
        return [case_date] * int(html_tree.xpath("count(//a[contains(./@href, '.pdf')])"))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree in self.html:
            docket_numbers.extend(self._return_docket_numbers(html_tree))
        return docket_numbers

    @staticmethod
    def _return_docket_numbers(html_tree):
        path = "//a[contains(./@href, '.pdf')]/text()"
        return list(html_tree.xpath(path))
