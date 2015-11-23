"""
Scraper for Florida 3rd District Court of Appeal
CourtID: flaapp3
Court Short Name: flaapp3

History:
 - 2014-07-21: Written by Andrei Chelaru
 - 2014-07-24: Reviewed by mlr
 - 2015-07-28: Updated by m4h7
"""

from datetime import date
import time

import certifi
from juriscraper.lib.string_utils import titlecase
import re
import requests
from lxml import html
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().year
        self.url = 'http://www.3dca.flcourts.org/Opinions/ArchivedOpinions.shtml'
        self.base_path = "//h3/following::text()[.='OPINIONS']/following::table[1]//tr"

    def _download(self, request_dict={}):
        html_l = super(Site, self)._download(request_dict)
        s = requests.session()
        html_trees = []
        # this path reads the row for the last month in that year
        path = "//th[contains(., '{year}')]/following::tr[1]/td[position()>1]/a[contains(., '/')]/@href".format(
            year=self.year
        )
        # to get all the dates in that page the following path can be used:
        # path = "//th/following::tr/td[position()>1]/a[contains(., '/')]/@href"
        for url in html_l.xpath(path):
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

    def _return_case_names(self, html_tree):
        path = "{base}/td[2]//text()[1]".format(base=self.base_path)
        return [titlecase(s.lower()) for s in html_tree.xpath(path)]

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            download_urls.extend(self._return_download_urls(html_tree))
        return download_urls

    def _return_download_urls(self, html_tree):
        path = "{base}/td[1]//a/@href".format(base=self.base_path)
        return list(html_tree.xpath(path))

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            case_dates.extend(self._return_dates(html_tree))
        return case_dates

    def _return_dates(self, html_tree):
        path = "//h3/text()"
        dates = []
        text = html_tree.xpath(path)[0]
        text = re.search('(\d{2}-\d{2}-\d{4})', text).group(1)
        case_date = date.fromtimestamp(time.mktime(time.strptime(text.strip(), '%m-%d-%Y')))
        dates.extend([case_date] * int(html_tree.xpath("count({base})".format(base=self.base_path))))
        return dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree in self.html:
            docket_numbers.extend(self._return_docket_numbers(html_tree))
        return docket_numbers

    def _return_docket_numbers(self, html_tree):
        docket_numbers = []
        for e in html_tree.xpath("{base}/td[1]//a".format(base=self.base_path)):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(s)
        return docket_numbers
