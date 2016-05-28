"""This site is pretty bad. Very little HTML; everything is separated by
<br> tags. There is currently a case at the bottom of the page from 2009
that has incomplete meta data. You can see it in the example document.
"""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www2.ca3.uscourts.gov/recentop/week/recprec.htm'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath('//a[contains(@href, "opinarch")]/text()')]

    def _get_download_urls(self):
        return [e for e in self.html.xpath('//a[contains(@href, "opinarch")]/@href')]

    def _get_case_dates(self):
        dates = []
        for text_string in self.html.xpath('//text()'):
            if not text_string.lower().startswith('filed'):
                continue
            else:
                date_string = text_string.split(' ')[1]
                date_string = date_string.strip().strip(',')
                dates.append(convert_date_string(date_string))
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
        for _ in range(0, len(self.case_names)):
            if 'recprec' in self.url:
                statuses.append('Published')
            elif 'recnonprec' in self.url:
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_lower_courts(self):
        lower_courts = []
        for e in self.html.xpath('//a[contains(@href, "opinarch")]'):
            text_strings = e.xpath('./following-sibling::text()[1]')
            text_string = ' '.join(text_strings)
            if text_string.lower().startswith('filed') or \
                                            text_string.strip() == '':
                lower_courts.append('Unknown')
            else:
                lower_courts.append(text_string.strip())
        return lower_courts
