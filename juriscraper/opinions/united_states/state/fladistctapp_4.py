#  Scraper for Florida 4th District Court of Appeal
# CourtID: flaapp4
# Court Short Name: flaapp4
# Author: Andrei Chelaru
# Reviewer: mlr
# History:
# - 2014-07-22: Created by Andrei Chelaru
# - 2014-10-17, mlr: Added support for days with "Special Issuances"
# - 2015-06-17, mlr: Fixes some regex problems and expands an XPath to be more lenient
# - 2015-07-29, m4h7: Tweaks to work on new site.
# - 2016-05-07, arderyp: adjustment to handle malformed code and parse dates properly

import re
import certifi
import requests
from lxml import html
from datetime import date
from lxml.html.clean import Cleaner

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    base_anchor_regex = '4D.*\d{2})([- ][A-Z\d].*'
    base_anchor_path = "//a[starts-with(normalize-space(.), '4D')]"

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().year
        self.url = 'http://www.4dca.org/opinions/{year}op.shtml'.format(year=self.year)

    def _download(self, request_dict={}):
        """Build html list for sub-pages' content

        Use main index page (self.url) to find sub-pages,
        and build list of tuples associating each sub-page's
        url with it's associated html
        """
        html_l = super(Site, self)._download(request_dict)
        s = requests.session()
        html_trees = []
        # this path reads the links for the last month in that year
        path = "id('opinions')//h2[string-length()>2][last()]/following::a[string-length()=10]/@href[not(contains(., 'pdf'))]"
        # to get all the dates in that page the following path can be used:
        # path = "id('opinions')//a[string-length()=10]"
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
            html_trees.append((html_tree, url))

        return html_trees

    def _get_case_names(self):
        case_names = []
        for html_tree, url in self.html:
            case_names.extend(self._extract_case_names_from_sub_page(html_tree))
        return case_names

    def _extract_case_names_from_sub_page(self, html_tree):
        regex = '(?:%s)' % self.base_anchor_regex
        path = "{base}//text()".format(base=self.base_anchor_path)
        return [re.search(regex, s).group(1) for s in html_tree.xpath(path) if s.strip()]

    def _get_download_urls(self):
        download_urls = []
        for html_tree, url in self.html:
            download_urls.extend(self._extract_download_url_from_sub_page(html_tree))
        return download_urls

    def _extract_download_url_from_sub_page(self, html_tree):
        path = "{base}/@href".format(base=self.base_anchor_path)
        return list(html_tree.xpath(path))

    def _get_case_dates(self):
        case_dates = []
        for html_tree, url in self.html:
            case_dates.extend(self._extract_dates_from_sub_page(html_tree, url))
        return case_dates

    def _extract_dates_from_sub_page(self, html_tree, url):
        """Extract dates from specific opinion list page.

        This method is messy and complex because the court's HTML is sloppy, non-standard,
        and often malformed. Additionally, on any given date's opinion list page, the court
        may post opinions that are actually for a different date.  Thus we can't simply
        exract all resources from the page and use the page's date as the opinions' date.
        Example: April 20th page that has an April 19th opinions published on it:
        http://www.4dca.org/opinions/April%202016/04-20-16/opinions%20released.shtml
        """
        # Find paragraph with date string text so we can loop over
        # paragraph's parent and analyze all child elements for opinions data
        contain_syntax = 'contains(normalize-space(text()), "%s")'
        strings_to_detect = ['OPINIONS RELEASED', 'SPECIAL ISSUANCE', 'Special Issuance']
        string_check = ' or '.join(contain_syntax % string for string in strings_to_detect)
        paragraph_check = 'strong/u[%s]' % string_check
        match = html_tree.xpath('//p/%s' % paragraph_check)

        if not match:
            raise Exception('Unable to parse html for fladistctapp_4 scraper')

        if match:
            dates_dict = {}
            parent = match[0].xpath('parent::*/parent::*/parent::*')[0]

            # Sometimes the court puts opinions in p tags, and other times
            # they use ul lists.  We need to handle both.
            for element in parent.xpath('p | ul'):

                # Detect date headers, these are all in p tags, as of the time of coding
                date_string_match = element.xpath('%s/text()' % paragraph_check)
                if date_string_match:
                    date = convert_date_string(date_string_match[0].split()[-1])
                    dates_dict[date] = 0

                else:
                    # Are we dealing with an html ul list?
                    if element.xpath('li'):
                        dates_dict[date] += 1

                    else:
                        # Remove br and strong tags, as court is known to produce malformed html
                        cleaner = Cleaner(style=True, remove_tags=['br', 'strong'])
                        element = cleaner.clean_html(element)
                        opinion_matches = element.xpath('a')
                        if opinion_matches:
                            dates_dict[date] += len(opinion_matches)


        # Build and return list of dates based on date:opinion distribution detected above
        dates = []
        for date, count in dates_dict.iteritems():
            dates.extend([date] * count)
        return dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree, url in self.html:
            docket_numbers.extend(self._extract_docket_numbers_from_sub_page(html_tree))
        return docket_numbers

    def _extract_docket_numbers_from_sub_page(self, html_tree):
        regex = '(%s)' % self.base_anchor_regex
        path = "{base}//text()".format(base=self.base_anchor_path)
        return [re.search(regex, e).group(1) for e in html_tree.xpath(path) if e.strip()]
