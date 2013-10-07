"""
Scraper for the Supreme Court of Tennessee
CourtID: tenn
Court Short Name: Tenn.
"""
from juriscraper.GenericSite import GenericSite
import time
from datetime import date
from lxml import html


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.tsc.state.tn.us/courts/supreme-court/opinions?page=0'
        self.court_id = self.__module__

    def _get_download_urls(self):
        return [t for t in self.html.xpath("//table//tr/td/a/@href")]

    def _get_case_names(self):
        return [t for t in self.html.xpath("//table//tr/td/a/text()")]

    def _get_lower_courts(self):
        return [t.strip() for t in self.html.xpath("//table//tr/td[2]/text()")]

    def _get_case_dates(self):
        dates = []
        for s in self.html.xpath('//table//tr/td[4]/span/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(s, '%m/%d/%y'))))
        return dates

    def _get_docket_numbers(self):
        return [t for t in self.html.xpath("//table//tr/td/div[./@class[contains(.,'number')]]/text()")]

    # Here we are using the 'judges' field to list the Authoring Judge.
    # It would be better for GenericSite to have an 'author' field and to put
    # these there.
    def _get_judges(self):
        judges = []
        for t in self.html.xpath('//table//tr/td/div/text()'):
            if 'Authoring' in t:
                # We strip the text 'Authoring Judge: '
                judges.append(t[17:])
            else:
                continue
        return judges

    def _get_lower_court_judges(self):
        trial_judges = []
        for t in self.html.xpath('//table//tr/td/div/text()'):
            if 'Trial' in t:
                # We strip the text 'Trial Court Judge: '
                trial_judges.append(t[19:])
            else:
                continue
        return trial_judges

    def _get_summaries(self):
        summaries = []
        for e in self.html.xpath('//table//tr/td//div/p'):
            s = html.tostring(e, method='text', encoding='unicode')
            summaries.append(s)
        return summaries

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)
