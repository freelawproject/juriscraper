from juriscraper.GenericSite import GenericSite
import time
from datetime import date
from juriscraper.lib.string_utils import titlecase

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.method = 'POST'
        self.parameters = {'age': '2'}
        self.url = "http://www.ca9.uscourts.gov/opinions/index.php"
        self.court_id = self.__module__

    def _get_case_names(self):
        path = '''//table[3]//tr[position() >= 2 and not(contains(child::td//text(), 
                "NO OPINIONS") or contains(child::td//text(), "NO MEMOS"))]/td[1]/a/text()'''
        return [titlecase(text) for text in self.html.xpath(path)]

    def _get_download_urls(self):
        path = '''//table[3]//tr[position() >= 2 and not(contains(child::td//text(), 
                "NO OPINIONS") or contains(child::td//text(), "NO MEMOS"))]/td[1]/a/@href'''
        return [e for e in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '''//table[3]//tr[position() >= 2 and not(contains(child::td//text(), 
                "NO OPINIONS") or contains(child::td//text(), "NO MEMOS"))]/td[6]//text()'''
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                    for date_string in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = '''//table[3]//tr[position() >= 2 and not(contains(child::td//text(), 
                "NO OPINIONS") or contains(child::td//text(), "NO MEMOS"))]/td[2]//text()'''
        return [docket_number for docket_number in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        for _ in range(0, len(self.case_names)):
            if 'opinion' in self.url.lower():
                statuses.append('Published')
            elif 'memoranda' in self.url.lower():
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_nature_of_suit(self):
        path = '''//table[3]//tr[position() >= 2 and not(contains(child::td//text(), 
                "NO OPINIONS") or contains(child::td//text(), "NO MEMOS"))]/td[4]//text()'''
        return [nature for nature in self.html.xpath(path)]

    def _get_lower_court(self):
        path = '''//table[3]//tr[position() >= 2 and not(contains(child::td//text(), 
                "NO OPINIONS") or contains(child::td//text(), "NO MEMOS"))]/td[3]//text()'''
        return [lc for lc in self.html.xpath(path)]
