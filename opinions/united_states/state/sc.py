"""Scraper for South Carolina Supreme Court
CourtID: sc
Court Short Name: S.C.
Author: TBM
Date created: 04-18-2014
"""

import re
from datetime import date
from datetime import datetime

from juriscraper.GenericSite import GenericSite


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        today = date.today()
        self.url = 'http://www.judicial.state.sc.us/opinions/indexSCPub.cfm?year=%s&month=%s' % (today.year, today.month)

    def _get_download_urls(self):
        path = '//div[@id="pageContentOpinionList"]//a[contains(@href, "HTMLFiles")]/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        path = '//div[@id="pageContentOpinionList"]//a[contains(@href, "HTMLFiles")]/text()'
        for txt in self.html.xpath(path):
            expression = '(.* - )(.*)'
            case_name = re.search(expression, txt, re.MULTILINE).group(2)
            case_names.append(case_name)
        return case_names

    def _get_case_dates(self):
        dates = []
        for node in self.html.xpath('//div[@id="pageContentOpinionList"]/node()[not(self::text())]'):
            try:
                tag_name = node.tag
                if tag_name == 'b':
                    # It's a header, grab the date and reset the counter
                    date_obj = datetime.strptime(node.text.strip().split(' ', 1)[0],
                                                 '%m-%d-%Y').date()
                elif tag_name == 'a':
                    # If it's a link, we've already got the correct date, so each time we have a link, append it to
                    # our list.
                    dates.append(date_obj)
                else:
                    continue
            except AttributeError:
                # Text node; something else
                tag_name = None  # Not essential, but reset this for the next iteration of the loop
                continue

        return dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        path = '//div[@id="pageContentOpinionList"]//a[contains(@href, "HTMLFiles")]/text()'
        for txt in self.html.xpath(path):
            expression = '(.* - )(.*)'
            docket_number = re.search(expression, txt,
                                      re.MULTILINE).group(1)
            docket_numbers.append(docket_number)
        return docket_numbers

    def _get_summaries(self):
        path = '//div[@id="pageContentOpinionList"]/blockquote/text()'
        return list(self.html.xpath(path))
