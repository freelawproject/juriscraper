# coding=utf-8
"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
"""

import certifi
import requests
from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    cases = []
    sub_page_opinion_link_path = "//a[@class='Head articletitle']"
    parent_summary_block_path = 'parent::p/following-sibling::div[@class="Normal"][1]'

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.cobar.org/For-Members/Opinions-Rules-Statutes/Colorado-Supreme-Court-Opinions"
        self.base_path = "//div[@id='dnn_ctr2509_ModuleContent']/ul/li/a"
        # dummy sequence to force one call to _download_backwards
        self.back_scrape_iterable = ['dummy']

    def _download(self, request_dict={}):
        html_l = super(Site, self)._download(request_dict)
        self.session = requests.session()
        self.request_dict = request_dict
        html_trees = []

        # Loop over sub-pages
        for ahref in html_l.xpath(self.base_path):
            # If testing, quit after first 2 samples
            # PLEASE NOTE: if adding a unique test case,
            # you will want to edit the example page's
            # HTML if need be to make sure that your
            # specific test subpage date falls within the
            # first three links on the self.url list page,
            # otherwise it won't be tested.
            if self.method == 'LOCAL' and len(html_trees) > 2:
                break

            date_string = ahref.xpath("./text()")[0]
            url = ahref.xpath("./@href")[0]
            date_obj = convert_date_string(date_string)
            logger.info("Getting sub-url: %s" % url)

            # Fetch sub-page's content
            request = self._get_resource(url)
            text = self._clean_text(request.text)
            html_tree = html.fromstring(text)
            html_tree.make_links_absolute(self.url)

            # Process the content
            remove_anchors = lambda url: url.split('#')[0]
            html_tree.rewrite_links(remove_anchors)
            self._extract_cases_from_sub_page(html_tree, date_obj)
            html_trees.append((html_tree, date_obj))

        return html_trees

    def _get_resource(self, resource_url):
        request = self.session.get(
            resource_url,
            headers={'User-Agent': 'Juriscraper'},
            verify=certifi.where(),
            **self.request_dict
        )
        request.raise_for_status()
        if request.encoding == 'ISO-8859-1':
            request.encoding = 'cp1252'
        return request

    def _extract_cases_from_sub_page(self, html_tree, date_obj):
        for anchor in html_tree.xpath("//a[@class='Head articletitle']"):
            text = self._extract_text_from_anchor(anchor)
            self.cases.append({
                'date': date_obj,
                'status': 'Published',
                'name': self._extract_name_from_anchor(anchor),
                'url': self._extract_url_from_anchor(anchor),
                'docket': self._extract_docket_from_text(text),
                'citation': self._extract_citation_from_text(text),
                'summary': self._extract_summary_relative_to_anchor(anchor),
                'nature': self._extract_nature_relative_to_anchor(anchor),
            })

    @staticmethod
    def _extract_docket_from_text(text):
        return text.split('No. ')[1].split('.')[0].rstrip('.').replace(' &', ',')

    @staticmethod
    def _extract_citation_from_text(text):
        return text.split('.')[0].strip()

    @staticmethod
    def _extract_text_from_anchor(anchor):
        text = anchor.xpath('text()')[0]
        text = text.replace('Nos.', 'No.')
        if 'No.' in text and 'No. ' not in text:
            text = text.replace('No.', 'No. ')
        return text

    @staticmethod
    def _extract_url_from_anchor(anchor):
        return anchor.xpath('@href')[0]

    def _extract_name_from_anchor(self, anchor):
        text = self._extract_text_from_anchor(anchor)
        try:
            name = text.split('. ', 3)[3]
        except:
            name = self._get_missing_name_from_resource(
                self._extract_url_from_anchor(anchor))
        return name.strip().rstrip('.')

    def _extract_summary_relative_to_anchor(self, anchor):
        parts = anchor.xpath('%s/p' % self.parent_summary_block_path)
        return ' '.join([part.text_content().strip() for part in parts])

    def _extract_nature_relative_to_anchor(self, anchor):
        """Extract italicized nature summary that appears directly after download url

        The court uses a lot of different html method of presenting this information.
        If a "nature" field is showing blank, it could be that they are using a new
        html path, which should be added to the path_patterns list below.
        """
        nature = ''

        # The order of this list matters.  Generally, put
        # the more complex paths as the top
        path_patterns = [
            '%s/p/strong/em/span/text()',
            '%s/p/em/text()',
            '%s/p/em/span/text()',
            '%s/p/i/span/text()',
            '%s/p/i/text()',
            '%s/em/text()',
            '%s/em/span/text()',
            '%s/p/span/i/text()',
            '%s/span/em/text()',
            '%s/p/strong/em/text()',
            '%s/strong/em/text()',
            '%s/span/text()',
            '%s/p/span/em/text()',
        ]
        for pattern in path_patterns:
            try:
                nature = anchor.xpath(pattern % self.parent_summary_block_path)[
                    0]
                break
            except:
                continue
        return nature.strip().rstrip('.')

    def _get_missing_name_from_resource(self, resource_url):
        """Extract case name from case document

        This is a fall back method that should only be called
        if the clerk made a mistake and forgot to put the case
        name on the resource/opinion list page. example:
        http://www.cobar.org/For-Members/Opinions-Rules-Statutes/Colorado-Supreme-Court-Opinions
        """
        request = self._get_resource(resource_url)
        text = self._clean_text(request.text)
        html_tree = html.fromstring(text)
        parts = html_tree.xpath(
            '//p/strong[starts-with(text(), "Plaintiff-Appellee:")]/parent::p/text()')
        return ' '.join(part.strip() for part in parts if part.strip())

    def _get_case_names(self):
        return [case['name'] for case in self.cases]

    def _get_download_urls(self):
        return [case['url'] for case in self.cases]

    def _get_case_dates(self):
        return [case['date'] for case in self.cases]

    def _get_docket_numbers(self):
        return [case['docket'] for case in self.cases]

    def _get_neutral_citations(self):
        return [case['citation'] for case in self.cases]

    def _get_precedential_statuses(self):
        return [case['status'] for case in self.cases]

    def _get_summaries(self):
        return [case['summary'] for case in self.cases]

    def _get_nature_of_suit(self):
        return [case['nature'] for case in self.cases]

    @staticmethod
    def cleanup_content(content):
        tree = html.fromstring(content)
        core_element = tree.xpath('//div[@id="dnn_ctr2513_ModuleContent"]')[0]
        return html.tostring(
            core_element,
            pretty_print=True,
            encoding='unicode'
        )

    def _download_backwards(self, _):
        # dummy backscrape parameter is ignored
        # should be called only once as it parses the whole page
        # and all subpages on every call
        self.base_path = "//table//td[1]/ul/li/strong/a"
        self.html = self._download()
