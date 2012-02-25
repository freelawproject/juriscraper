import ca9p
import time
from datetime import date

class Site(ca9p.Site):
    '''The unpublished cases have one more column than the published. Thus some
    overriding is done here. More than usual, but it's very slight tweaks.'''
    def __init__(self):
        super(Site, self).__init__()
        self.url = "http://www.ca9.uscourts.gov/memoranda/?o_mode=view&amp;o_sort_field=21&amp;o_sort_type=DESC&o_page_size=100"
        self.court_id = self.__module__

    def _get_case_dates(self):
        path = '''//table[3]//tr[position() >= 2 and not(contains(child::td//text(), 
                "NO OPINIONS") or contains(child::td//text(), "NO MEMOS"))]/td[7]//text()'''
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
                    for date_string in self.html.xpath(path)]

    def _get_nature_of_suit(self):
        path = '''//table[3]//tr[position() >= 2 and not(contains(child::td//text(), 
                "NO OPINIONS") or contains(child::td//text(), "NO MEMOS"))]/td[5]//text()'''
        return [nature for nature in self.html.xpath(path)]

    def _get_lower_court(self):
        path = '''//table[3]//tr[position() >= 2 and not(contains(child::td//text(), 
                "NO OPINIONS") or contains(child::td//text(), "NO MEMOS"))]/td[4]//text()'''
        return [lc for lc in self.html.xpath(path)]
