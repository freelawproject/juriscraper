# coding=utf-8
"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Asadullah Baig<asadullahbeg@outlook.com>
Reviewer: mlr
Date created: 2014-07-11
"""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import clean_string
import re
from datetime import date
from lxml import html


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.crawl_date = date.today()
        self.url = 'http://www.cobar.org/opinions/opinionlist.cfm?casedate={month}/{day}/{year}&courtid=2'.format(
            month=self.crawl_date.month,
            day=self.crawl_date.day,
            year=self.crawl_date.year,
        )
        # For testing
        #self.url = 'http://www.cobar.org/opinions/opinionlist.cfm?casedate=6/30/2014&courtid=2'
        self.court_id = self.__module__

    def _get_case_names(self):
        return self._get_data_by_grouping_name('case_names')

    def _get_download_urls(self):
        path = "//div[@id='opinion']/p/a/@href[contains(., 'opinion.cfm')]"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        count = len(self.html.xpath('//div[@id="opinion"]/p/a/b//text()'))
        return [self.crawl_date] * count

    def _get_docket_numbers(self):
        return self._get_data_by_grouping_name('docket_numbers')

    def _get_neutral_citations(self):
        return self._get_data_by_grouping_name('neutral_citations')

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_summaries(self):
        path_to_all_paras = '//div[@id="opinion"]/p'
        summaries = []
        summary_parts = ''
        for elem in self.html.xpath(path_to_all_paras):
            # Check if it's a title paragraph
            if elem.xpath('./a/b//text()'):
                # If so, append previous values and start a new summary item.
                if summary_parts:
                    summaries.append(summary_parts)
                summary_parts = ''
                continue
            # Check if it has a descendant with font[@size="2"].
            elif elem.xpath('./font[@size="2"]'):
                # If so, then it's a summary paragraph.
                summary_parts += '<p>%s</p>\n' % clean_string(html.tostring(elem, method='text', encoding='unicode'))
            else:
                # Something else...
                continue

        # Append the tailing summary
        if summary_parts:
            # On days with no content, this winds up blank and shouldn't be appended.
            summaries.append(summary_parts)
        return summaries

    def _get_nature_of_suit(self):
        path = '//div[@id="opinion"]//b/i/text()'
        natures = []
        for nature_str in self.html.xpath(path):
            natures.append(', '.join(nature_str.split(u'—')))
        return natures

    def _get_data_by_grouping_name(self, group_name):
        """Returns the requested meta data from the HTML by finding the titles and extracting the requested piece of
        meta data.

        Titles look like:
           2014 COA 80. No. 07CA1217. People v. Schupper.
        """
        path = '//div[@id="opinion"]/p/a/b//text()'
        meta_data = []
        regex = re.compile(r'(?P<neutral_citations>.*)\. (?P<docket_numbers>(?:Nos?\.)?.*\d{2})\. (?P<case_names>.*)\.')
        for title in self.html.xpath(path):
            title = ' '.join(title.split())
            print title
            value = regex.search(title).group(group_name)
            meta_data.append(value)
        return meta_data


