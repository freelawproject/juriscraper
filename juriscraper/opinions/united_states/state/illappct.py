# Author: Krist Jin
# 2013-08-18: Created.
# 2014-07-17: Updated by mlr to remedy InsanityException.

from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.state.il.us/court/Opinions/recent_appellate.asp'
        self.base_path = '//table[@class="content"]//table//tr[not(name(..)="thead") and descendant::a][count(td) = 5]'

    def _get_download_urls(self):
        path = self.base_path + '/td[5]//a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath(self.base_path + '/td[5]//a[normalize-space(text())]'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(s)
        return case_names

    def _get_case_dates(self):
        path = self.base_path + '/td[1]/div/text()'
        return [convert_date_string(date_string) for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath(self.base_path + '/td[3]'):
            s = html.tostring(e, method='text', encoding='unicode')
            if 'Rel' in s:
                statuses.append('Unpublished')
            else:
                statuses.append('Published')
        return statuses

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath(self.base_path + '/td[3]'):
            s = html.tostring(e, method='text', encoding='unicode')
            s = ' '.join(s.split())
            s = s.replace("Official Reports", "")
            s = s.replace("NRel", "")
            docket_numbers.append(s)
        return docket_numbers

    def _get_neutral_citations(self):
        neutral_citations = []
        for e in self.html.xpath(self.base_path + '/td[4]'):
            s = html.tostring(e, method='text', encoding='unicode')
            neutral_citations.append(s)
        return neutral_citations

