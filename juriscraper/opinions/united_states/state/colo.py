# coding=utf-8
"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Asadullah Baig <asadullahbeg@outlook.com>
Reviewer: mlr
Date created: 2014-07-11
"""

import re
import certifi
import requests
from lxml import html
from datetime import date

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.cobar.org/opinions/index.cfm?courtid=2'
        # For testing
        #self.url = 'http://www.cobar.org/opinions/opinionlist.cfm?casedate=6/30/2014&courtid=2'
        self.court_id = self.__module__
        self.title_regex = re.compile(r'(?P<neutral_citations>.*?)\. '
                                      r'(?P<docket_numbers>(?:Nos?\.)?.*\d{1,2})(\.)? '
                                      r'(?P<case_names>.*)\.')
        self.path = "//table//td[1]/ul/li[position() <= 5]/strong/a"
        # dummy sequence to force one call to _download_backwards
        self.back_scrape_iterable = ['dummy']

    def _download(self, request_dict={}):
        if self.method == 'LOCAL':
            # Note that this is returning a list of HTML tree-date pairs.
            html_trees = [
                (
                    super(Site, self)._download(request_dict=request_dict),
                    date.today(),
                ),
            ]
        else:
            html_l = super(Site, self)._download(request_dict)
            s = requests.session()
            html_trees = []
            for ahref in html_l.xpath(self.path):
                text = ahref.xpath("./text()")[0]
                url = ahref.xpath("./@href")[0]
                parsed_date = convert_date_string(text)
                logger.info("Getting sub-url: %s" % url)
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
                html_trees.append((html_tree, parsed_date))
        return html_trees

    def _get_case_names(self):
        return self._get_data_by_grouping_name('case_names')

    def _get_download_urls(self):
        path = "//div[@id='opinion']/p/a/@href[contains(., 'opinion.cfm')]"
        urls = []
        for tree, _ in self.html:
            urls += list(tree.xpath(path))
        return urls

    def _get_case_dates(self):
        case_dates = []
        for tree, parsed_date in self.html:
            count = len(tree.xpath('//div[@id="opinion"]/p/a/b//text()'))
            case_dates += [parsed_date] * count
        return case_dates

    def _get_docket_numbers(self):
        return self._get_data_by_grouping_name('docket_numbers')

    def _get_neutral_citations(self):
        return self._get_data_by_grouping_name('neutral_citations')

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    # Removed by mlr on 2015-10-16. Unfortunately, this code is complicated and
    # fails in practice. There's no easy way to identify what's a paragraph,
    # and so covering every corner case is near impossible. We can bring it back
    # someday, but make sure it works for 2015-09-14 as well as 2015-6-1.
    # def _get_summaries(self):
    #     path_to_all_paras = '//div[@id="opinion"]/p'
    #     summaries = []
    #     for tree, _ in self.html:
    #         summary_parts = ''
    #         paragraphs = tree.xpath(path_to_all_paras)
    #         for elem in paragraphs:
    #             el_summary = ''
    #             # Check if it has a descendant with font[@size="2"].
    #             for descendant in ('./font[@size="2"]',
    #                                './font[@size="1"]',
    #                                './font[@sizes="2"]'):
    #                 el = elem.xpath(descendant)
    #                 if el:
    #                     # If so, then it's a summary paragraph.
    #                     el_summary += '<p>%s</p>\n' % clean_string(html.tostring(el[0], method='text', encoding='unicode'))
    #                     break
    #             # Check if it's a title paragraph
    #             if elem.xpath('./a/b//text()'):
    #                 # If so, append previous values and start a new summary item
    #                 if summary_parts:
    #                     summaries.append(summary_parts)
    #                     summary_parts = ''
    #                 if el_summary:
    #                     summaries.append(el_summary)
    #                     el_summary = ''
    #             if el_summary:
    #                 summary_parts += el_summary
    #
    #         # Append the tailing summary
    #         if summary_parts:
    #             # On days with no content, this winds up blank and shouldn't be
    #             # appended.
    #             summaries.append(summary_parts)
    #     return summaries

    def _get_nature_of_suit(self):
        path = '//div[@id="opinion"]//b/i/text()'
        natures = []
        for tree, _ in self.html:
            for nature_str in tree.xpath(path):
                natures.append(', '.join(nature_str.split(u'—')))
        return natures

    def _get_data_by_grouping_name(self, group_name):
        """Returns the requested meta data from the HTML by finding the titles
        and extracting the requested piece of meta data.

        Titles look like:
           2014 COA 80. No. 07CA1217. People v. Schupper.
        """
        path = '//div[@id="opinion"]/p/a/b//text()'
        meta_data = []
        for tree, _ in self.html:
            for title in tree.xpath(path):
                title = ' '.join(title.split())
                value = self.title_regex.search(title).group(group_name)
                if group_name == 'docket_numbers':
                    # Dual docket numbers should be comma delimited, not ampersand
                    value = value.replace(' & ', ', ')
                    #Clean up typos where clerk forgot space between period and number
                    if '.' in value and '. ' not in value:
                        value = value.replace('.', '. ')
                meta_data.append(value)
        return meta_data

    @staticmethod
    def cleanup_content(content):
        tree = html.fromstring(content)
        return html.tostring(
            tree.xpath("//*[@id='opinion']")[0],
            pretty_print=True,
            encoding='unicode'
        )

    def _download_backwards(self, _):
        # dummy backscrape parameter is ignored
        # should be called only once as it parses the whole page
        # and all subpages on every call
        self.path = "//table//td[1]/ul/li/strong/a"
        self.html = self._download()
