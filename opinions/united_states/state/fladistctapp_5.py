"""
Scraper for Florida 5th District Court of Appeal
CourtID: flaapp5
Court Short Name: flaapp5
Author: Andrei Chelaru
Reviewer: mlr
History:
 - 2014-07-23, Andrei Chelaru: Created.
 - 2014-08-05, mlr: Updated.
 - 2014-08-06, mlr: Updated.
 - 2014-09-18, mlr: Updated date parsing code to handle Sept.
 - 2016-03-16, arderyp: Updated to return proper absolute pdf url paths, simplify date logic
"""

import re
import certifi
import requests
from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.5dca.org/opinions_archived.shtml'
        self.base_path = "//a"
        self.case_regex = '(5D.*-.*\d{1,3})([- ]+[A-Za-z].*)'

    def _download(self, request_dict={}):
        html_l = super(Site, self)._download(request_dict)
        s = requests.session()
        html_trees = []
        # this path reads the link of the last 2 dates
        path = "(//a[contains(./@href, 'filings')])[position() < 3]/@href"
        # to get all the dates in that page the following path can be used:
        # path = "//a[contains(./@href, 'filings')]"
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
            html_tree.make_links_absolute(url)

            # This district has some nasty HTML that occasionally breaks one case name across two anchors.
            # For example (http://www.5dca.org/Opinions/Opin2014/072114/filings%20072114.html):
            #
            #      <a href='...'>5D12-4340, 5D12-4401 and 5D12-4319</a><br>
            #      <a href='...'>N.R. v. Florida Birth-Related</a>
            #
            # The solution is to look at all the a's, and merge the text when the href's are identical.
            previous_a = None
            for e in html_tree.xpath('//a'):
                if previous_a is not None and e.attrib['href'] == previous_a.attrib['href']:
                    # Same. Merge their text then delete the extraneous element.
                    previous_text = html.tostring(previous_a, method='text', encoding='unicode')
                    e_text = html.tostring(e, method='text', encoding='unicode')
                    previous_a.text = " ".join((previous_text + e_text).split())

                    # See: http://stackoverflow.com/a/7981894/64911
                    e.getparent().remove(e)
                previous_a = e

            html_trees.append(html_tree)
        return html_trees

    def _get_case_names(self):
        case_names = []
        for html_tree in self.html:
            case_names.extend(self._return_case_names(html_tree))
        return case_names

    def _return_case_names(self, html_tree):
        path = "{base}/text()".format(base=self.base_path)
        # Uncomment for inevitable regex debugging.
        # for s in html_tree.xpath(path):
        #     print "s: %s" % s
        #     re.search(self.case_regex, s).group(2)
        return [re.search(self.case_regex, s).group(2) for s in html_tree.xpath(path)]

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            download_urls.extend(self._return_download_urls(html_tree))
        return download_urls

    def _return_download_urls(self, html_tree):
        path = "{base}/@href".format(base=self.base_path)
        return list(html_tree.xpath(path))

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            case_dates.extend(self._return_dates(html_tree))
        return case_dates

    def _return_dates(self, html_tree):
        path = "//*[starts-with(., 'Opinions')]/text()"
        text = html_tree.xpath(path)[0]
        date_string = re.search('.* Week of (.*)', text).group(1).strip()
        case_date = convert_date_string(date_string)
        count = int(html_tree.xpath("count({base})".format(base=self.base_path)))
        return [case_date for i in range(count) ]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree in self.html:
            docket_numbers.extend(self._return_docket_numbers(html_tree))
        return docket_numbers

    def _return_docket_numbers(self, html_tree):
        path = "{base}/text()".format(base=self.base_path)
        return [re.search(self.case_regex, e).group(1) for e in html_tree.xpath(path)]
