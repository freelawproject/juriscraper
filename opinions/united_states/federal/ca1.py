from GenericSite import GenericSite
import re
import time
from datetime import date
from lxml import html

class Site(GenericSite):
    def __init__(self):
        self.urls = ('http://www.ca1.uscourts.gov/opinions/opinionrss.php',)
        super(Site, self).__init__()

    def _get_download_links(self):
        return [html.tostring(e, method='text') for e in self.html.xpath('//item/link')]

    def _get_case_names(self):
        regex = re.compile("(\d{2}-.*?\W)(.*)$")
        return [regex.search(html.tostring(e, method='text')).group(2)
                                  for e in self.html.xpath('//item/title')]

    def _get_case_dates(self):
        dates = []
        for e in self.html.xpath('//item/pubdate'):
            date_string = html.tostring(e, method='text').split()[0]
            dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%Y-%m-%d'))))
        return dates

    def _get_docket_numbers(self):
        regex = re.compile("(\d{2}-.*?\W)(.*)$")
        return [regex.search(html.tostring(e, method='text')).group(1)
                                  for e in self.html.xpath('//item/title')]

    def _get_neutral_citations(self):
        pass

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath("//item/category"):
            text = html.tostring(e, method='text').lower().strip()
            if "unpublished" in text:
                statuses.append("Unpublished")
            elif "published" in text:
                statuses.append("Published")
            elif "errata" in text:
                statuses.append("Errata")
            else:
                statuses.append("Unknown")
        return statuses

    def _text_clean(self, text):
        # this function provides the opportunity to clean text before it's made
        # into an HTML tree.
        text = re.sub(r'<!\[CDATA\[', '', text)
        text = re.sub(r'\]\]>', '', text)
        return text

    def _pre_clean(self, dirty_html):
        '''Any cleanup code that is needed for the court lives here, for example
        in the case of ca1, we need to flip the sort order of the item elements.
        '''
        clean_html = dirty_html

        return clean_html
