# History:
#   2013-08-16: Created by Krist Jin
#   2014-12-02: Updated by Mike Lissner to remove the summaries code.
#   2016-02-26: Updated by arderyp: simplified thanks to new id attribute identifying decisions table
#   2016-03-27: Updated by arderyp: fixed to handled non-standard formatting

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.state.il.us/court/Opinions/recent_supreme.asp'

    def _get_download_urls(self):
        path = '%s//a[1]/@href' % self._get_decisions_table_cell_path(5)
        return [href for href in self.html.xpath(path)]

    def _get_case_names(self):
        path = '%s//a[1]/text()' % self._get_decisions_table_cell_path(5)
        return [text for text in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '%s//div/text()' % self._get_decisions_table_cell_path(1)
        return [convert_date_string(date_string) for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        path = '%s//div' % self._get_decisions_table_cell_path(3)
        for div in self.html.xpath(path):
            text = div.xpath('strong/text()')
            if text and 'NRel' in text:
                statuses.append('Unpublished')
            else:
                statuses.append('Published')
        return statuses

    def _get_docket_numbers(self):
        docket_numbers = []
        path = '%s//div' % self._get_decisions_table_cell_path(3)
        for div in self.html.xpath(path):
            text = div.xpath('text()')
            text = ''.join(text).replace('cons.', '')
            docket_numbers.append(' '.join(text.split()))
        return docket_numbers

    def _get_neutral_citations(self):
        path = '%s//div/text()' % self._get_decisions_table_cell_path(4)
        return [text for text in self.html.xpath(path)]

    def _get_decisions_table_cell_path(self, cell_number):
        """return path to Nth cell of each row in decisions table"""
        return '//table[@id="decisions"]//tr/td[%s]' % str(cell_number)
