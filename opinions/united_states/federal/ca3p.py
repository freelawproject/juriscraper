from GenericSite import GenericSite
import time
from datetime import date
from lxml import html

class Site(GenericSite):
    '''This site is pretty bad. Very little HTML; everything is separated by 
    <br> tags. There is currently a case at the bottom of the page from 2009 
    that has incomplete meta data. You can see it in the example document, but 
    that is why all methods return a sliced array.
    '''
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.ca3.uscourts.gov/recentop/week/recprec.htm'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath('//a[contains(@href, "opinarch")]/text()')]

    def _get_download_links(self):
        return [e for e in self.html.xpath('//a[contains(@href, "opinarch")]/@href')]

    def _get_case_dates(self):
        dates = []
        for text_string in self.html.xpath('//text()'):
            if not text_string.lower().startswith('filed'):
                continue
            else:
                date_string = text_string.split(' ')[1]
                date_string = date_string.strip().strip(',')
                dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%y'))))
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for text_string in self.html.xpath('//text()'):
            if not text_string.lower().startswith('filed'):
                continue
            else:
                docket_numbers.append(text_string.split(' ')[3])
        return docket_numbers

    def _get_precedential_statuses(self):
        statuses = []
        for status in range(0, len(self.case_names)):
            if 'recprec' in self.url:
                statuses.append('Published')
            elif 'recnonprec' in self.url:
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_lower_courts(self):
        lower_courts = []
        for text_string in self.html.xpath('//a[contains(@href, "opinarch")]/following-sibling::text()'):
            if text_string.lower().startswith('filed'):
                continue
            else:
                lower_courts.append(text_string.strip())
        if 'recprec' in self.url:
            # The precedential page has a rogue value on the bottom that we 
            # need a special case for.
            lower_courts.append("Unknown")
        return lower_courts
