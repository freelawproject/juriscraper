"""
Scraper for Florida 5th District Court of Appeal
CourtID: flaapp5
Court Short Name: flaapp5
Court Contact: 5dca@flcourts.org, 386-947-1530
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
from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.lib.string_utils import normalize_dashes
from juriscraper.lib.string_utils import clean_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.5dca.org/opinions_archived.shtml'
        self.base_path = "//a"
        self.case_regex = '(5D.*-.*\d{1,3})([- ]+[A-Za-z1-9].*)'

    def _download(self, request_dict={}):
        html_l = super(Site, self)._download(request_dict)

        # Test/example files should use html from direct resource page
        # NOTE: fladistctapp_5_example_5.html SHOULD have 0 results
        if self.method == 'LOCAL':
            return [html_l]

        html_trees = []
        # this path reads the link of the last 2 dates
        path = "(//a[contains(./@href, 'filings')])[position() < 3]/@href"
        # to get all the dates in that page the following path can be used:
        # path = "//a[contains(./@href, 'filings')]"
        for url in html_l.xpath(path):
            html_tree = self._get_html_tree_by_url(url, request_dict)

            # This district has some nasty HTML that occasionally breaks one
            # case name across two anchors. For example (http://www.5dca.org/Opinions/Opin2014/072114/filings%20072114.html):
            #
            #      <a href='...'>5D12-4340, 5D12-4401 and 5D12-4319</a><br>
            #      <a href='...'>N.R. v. Florida Birth-Related</a>
            #
            # The solution is to look at all the a's, and merge the text when
            # the href's are identical.
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
        names = []
        for anchor in self._return_anchors_with_text(html_tree):
            text = self.sanitize_text(anchor.text_content().strip())
            names.append(re.search(self.case_regex, text).group(2))
        return names

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            download_urls.extend(self._return_download_urls(html_tree))
        return download_urls

    def _return_download_urls(self, html_tree):
        return [a.xpath('@href')[0] for a in self._return_anchors_with_text(html_tree)]

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            dates = self._return_dates(html_tree)
            if dates:
                case_dates.extend(dates)
        return case_dates

    def _return_dates(self, html_tree):
        prefixes = ['Opinions', 'OPINIONS', 'Opinion', 'OPINION']
        paths = ["//*[starts-with(., '%s ')]/text()" % string for string in prefixes]
        path = ' | '.join(paths)
        date_text = html_tree.xpath(path)
        # Some pages have only PCAS publications without opinions
        # example: http://www.5dca.org/Opinions/Opin2016/092616/filings%20092616.html
        if not date_text:
            return False
        text = date_text[0].lower()
        date_string = re.search('.* week of (.*)', text).group(1).strip()
        case_date = convert_date_string(date_string)
        return [case_date] * len(self._return_anchors_with_text(html_tree))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree in self.html:
            docket_numbers.extend(self._return_docket_numbers(html_tree))
        return docket_numbers

    def _return_docket_numbers(self, html_tree):
        dockets = []
        for anchor in self._return_anchors_with_text(html_tree):
            text = self.sanitize_text(anchor.text_content().strip())
            docket_raw = re.search(self.case_regex, text).group(1)
            docket_clean = docket_raw.replace('&', '').replace(',', '')
            dockets.append(', '.join(docket_clean.split()))
        return dockets

    # Sometimes the html includes empty anchors,
    # we should only process href for anchors with text
    def _return_anchors_with_text(self, html_tree):
        return [a for a in html_tree.xpath(self.base_path) if a.text_content().strip()]

    def sanitize_text(self, text):
        """Prevent non-standard characters and typos from breaking regex"""
        return self.fix_court_year_id_typo(clean_string(normalize_dashes(text)))

    def fix_court_year_id_typo(self, text):
        """Work around court typo
        String missing leading '5', see fladistctapp_5_example_7.html
        Will return the same exact string 99.99% of the time
        """
        court_year_id = text.split('-')[0]
        if len(court_year_id) == 3 and court_year_id[0] == 'D':
            text = '5%s' % text
        return text
