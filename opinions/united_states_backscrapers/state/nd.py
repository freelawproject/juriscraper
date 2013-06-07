# Author: Michael Lissner
# Date created: 2013-06-06

import re
from datetime import date
from datetime import datetime

from juriscraper.opinions.united_states.state import nd


class Site(nd.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        today = date.today()
        self.url = 'http://www.ndcourts.gov/opinions/month/%s.htm' % (today.strftime("%b%Y"))

    def _get_download_urls(self):
        if self.crawl_date >= date(1998, 10, 1):
            path = '//a/@href'
        else:
            path = '//ul//a/@href'
        download_urls = []
        for html_link in self.html.xpath(path):
            case_number = re.search('(\d+)', html_link).group(0)
            download_urls.append('http://www.ndcourts.gov/wp/%s.wpd' % case_number)
        return download_urls

    def _get_case_names(self):
        if self.crawl_date >= date(1998, 10, 1):
            path = '//a/text()'
            return list(self.html.xpath(path))
        else:
            path = '//ul//a/text()'
            names = self.html.xpath(path)
            case_names = []
            if self.crawl_date < date(1996, 11, 1):
                # A bad time.
                for name in names:
                    name = name.rsplit('-')[0]
                    case_names.append(name)
                return case_names
            else:
                return list(names)

    def _get_case_dates(self):
        # A tricky one. We get the case dates, but each can have different number of cases below it, so we have to
        # count them.
        case_dates = []
        if self.crawl_date >= date(1998, 10, 1):
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
        else:
            path = '//h4|//li'
            for e in self.html.xpath(path):
                if e.tag == 'h4':
                    date_str = e.text
                    dt = datetime.strptime(date_str, '%B %d, %Y').date()
                elif e.tag == 'li':
                    try:
                        case_dates.append(dt)
                    except NameError:
                        # When we don't yet have the date
                        continue
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        if self.crawl_date >= date(1998, 10, 1):
            path = '//a/@href'
        else:
            path = '//ul//a/@href'
        docket_numbers = []
        for html_link in self.html.xpath(path):
            docket_numbers.append(re.search('(\d+)', html_link).group(0))
        return docket_numbers

    def _get_neutral_citations(self):
        if self.crawl_date < date(1997, 02, 01):
            # Old format, but no neutral cites, thus short circuit the function.
            return None
        elif self.crawl_date < date(1998, 10, 01):
            # Old format with: 1997 ND 30 - Civil No. 960157 or 1997 ND 30
            path = '//h4|//li/text()'
        elif self.crawl_date >= date(1998, 10, 1):
            # New format with: 1997 ND 30
            path = '//body/text()'
        neutral_cites = []
        for t in self.html.xpath(path):
            try:
                neutral_cites.append(re.search('(\d{4} ND (?:App)? \d{1,4})', t).group(0))
            except AttributeError:
                continue
        return neutral_cites

    def _post_parse(self):
        # Remove any information that applies to appellate cases.
        neutral_cites_copy = list(self.neutral_citations)
        for i in range(0, len(neutral_cites_copy)):
            if 'App' in neutral_cites_copy[i]:
                del self.download_urls[i]
                del self.case_names[i]
                del self.case_dates[i]
                del self.precedential_statuses[i]
                del self.docket_numbers[i]
                del self.neutral_citations[i]

    def _download_backwards(self, d):
        self.crawl_date = d
        self.url = 'http://www.ndcourts.gov/opinions/month/%s.htm' % (d.strftime("%b%Y"))
        self.html = self._download()
