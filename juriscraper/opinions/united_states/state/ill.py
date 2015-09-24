# History:
#   2013-08-16: Created by Krist Jin
#   2014-12-02: Updated by Mike Lissner to remove the summaries code.

from datetime import datetime

from lxml import html
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.state.il.us/court/Opinions/recent_supreme.asp'

    def _get_download_urls(self):
        path = '//td[@class="center"]/table[3]//a[contains(@href,".pdf")]/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//td[@class="center"]/table[3]//a[contains(@href,".pdf")]'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(s)
        return case_names

    def _get_case_dates(self):
        path = '//td[@class="center"]/table[3]//tr/td[1]//div/text()'
        return [datetime.strptime(date_string, '%m/%d/%y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath('//td[@class="center"]/table[3]//tr/td[3]//div/strong[normalize-space(text())]'):
            s = html.tostring(e, method='text', encoding='unicode')
            if 'NRel' in s:
                statuses.append('Unpublished')
            else:
                statuses.append('Published')
        return statuses

    def _get_docket_numbers(self):
        docket_numbers = []
        for s in self.html.xpath('//td[@class="center"]/table[3]//tr/td[3]/div/text()[not(preceding-sibling::br)]'):
            s = " ".join(s.split())
            if s:
                docket_numbers.append(s)
        return docket_numbers

    def _get_neutral_citations(self):
        neutral_citations = []
        for e in self.html.xpath('//td[@class="center"]/table[3]//tr/td[4]/div'):
            s = html.tostring(e, method='text', encoding='unicode')
            neutral_citations.append(s)
        return neutral_citations
