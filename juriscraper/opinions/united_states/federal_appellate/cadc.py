from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date
from lxml import html

class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.cadc.uscourts.gov/internet/opinions.nsf/uscadcopinions.xml'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath('//item/description/text()')]

    def _get_download_urls(self):
        return [html.tostring(e, method='text') for e in self.html.xpath('//item/link')]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath('//item/pubdate/text()'):
            date_only = ' '.join(date_string.split(' ')[1:4])
            dates.append(date.fromtimestamp(time.mktime(time.strptime(date_only, '%d %b %Y'))))
        return dates

    def _get_docket_numbers(self):
        return [e.split('|')[0] for e in self.html.xpath('//item/title/text()')]

    def _get_precedential_statuses(self):
        return ["Published" for _ in range(0, len(self.case_names))]
