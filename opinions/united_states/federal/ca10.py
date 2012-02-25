from GenericSite import GenericSite
import time
from datetime import date
from lxml import html

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.ca10.uscourts.gov/opinions/new/daily_decisions.rss'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath('//item/title/text()')]

    def _get_download_links(self):
        return [html.tostring(e, method='text') for e in self.html.xpath('//item/link')]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath('//item/pubdate/text()'):
            date_only = ' '.join(date_string.split(' ')[1:4])
            dates.append(date.fromtimestamp(time.mktime(time.strptime(date_only, '%d %b %Y'))))
        return dates

    def _get_docket_numbers(self):
        return [e.split(':')[1] for e in self.html.xpath('//item/description/text()[1]')]

    def _get_precedential_statuses(self):
        return [e for e in self.html.xpath('//item/category/text()')]

    def _get_lower_courts(self):
        return [e for e in self.html.xpath('//item/description/b/text()')]
