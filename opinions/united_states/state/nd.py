# Author: Michael Lissner
# Date created: 2013-06-06
# Updated: 2013-07-01 (make it abort on 1st of month before 4pm)

import re
from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.GenericSite import GenericSite


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        today = date.today()
        now = datetime.now()
        if today.day == 1 and now.hour < 16:
            # On the first of the month, the page doesn't exist until later in the day, so when that's the case,
            # we don't do anything until after 16:00. If we try anyway, we get a 503 error. This simply aborts the
            # crawler.
            self.status = 200
            self.html = html.fromstring('<html></html>')
        else:
            self.url = 'http://www.ndcourts.gov/opinions/month/%s.htm' % (today.strftime("%b%Y"))

    def _get_download_urls(self):
        path = '//a/@href[contains(., "/court/opinions/")]'
        download_urls = []
        for html_link in self.html.xpath(path):
            case_number = re.search('(\d+)', html_link).group(0)
            download_urls.append('http://www.ndcourts.gov/wp/%s.wpd' % case_number)
        return download_urls

    def _get_case_names(self):
        path = '//a[contains(@href, "/court/opinions/")]/text()'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        # A tricky one. We get the case dates, but each can have different number of cases below it, so we have to
        # count them.
        test_path = '//body/a'
        if len(self.html.xpath(test_path)) == 0:
            # It's a month with no cases (like Jan, 2009). Early exit.
            return []
        case_dates = []
        path = '//body/a|//body/font'
        for e in self.html.xpath(path):
            if e.tag == 'font':
                date_str = e.text
                dt = datetime.strptime(date_str, '%B %d, %Y').date()
            elif e.tag == 'a':
                try:
                    case_dates.append(dt)
                except NameError:
                    # When we don't yet have the date
                    continue
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//a/@href[contains(., "/court/opinions/")]'
        docket_numbers = []
        for html_link in self.html.xpath(path):
            try:
                docket_numbers.append(re.search('(\d+)', html_link).group(0))
            except AttributeError:
                continue
        return docket_numbers

    def _get_neutral_citations(self):
        neutral_cites = []
        for t in self.html.xpath('//body/text()'):
            try:
                cite = re.search('^.{0,5}(\d{4} ND (?:App )?\d{1,4})', t, re.MULTILINE).group(1)
                neutral_cites.append(cite)
            except AttributeError:
                continue
        return neutral_cites

    def _post_parse(self):
        # Remove any information that applies to non-appellate cases.
        if self.neutral_citations:
            delete_items = []
            for i in range(0, len(self.neutral_citations)):
                if 'App' in self.neutral_citations[i]:
                    delete_items.append(i)

            for i in sorted(delete_items, reverse=True):
                del self.download_urls[i]
                del self.case_names[i]
                del self.case_dates[i]
                del self.precedential_statuses[i]
                del self.docket_numbers[i]
                del self.neutral_citations[i]
        else:
            # When there aren't any neutral cites that means everything is a supreme court case.
            pass
