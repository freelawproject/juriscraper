"""Scraper for the Supreme Court of Delaware
CourtID: del

Creator: Andrei Chelaru
Reviewer: mlr
"""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://courts.delaware.gov/opinions/list.aspx?ag=supreme%20court'
        # Note that we can't do the usual thing here because 'del' is a Python keyword.
        self.court_id = 'juriscraper.opinions.united_states.state.del'

    def _get_case_dates(self):
        return [convert_date_string(date.strip()) for date in self._get_nth_cell_data(2, text=True)]

    def _get_download_urls(self):
        return [url.strip() for url in self._get_nth_cell_data(1, href=True)]

    def _get_case_names(self):
        return [name.strip() for name in self._get_nth_cell_data(1, link_text=True)]

    def _get_docket_numbers(self):
        return [docket.strip() for docket in self._get_nth_cell_data(3, link_text=True)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_judges(self):
        # We need special logic here because they use <br> tags in the cell text
        return [' '.join(cell.xpath('text()')) for cell in self.html.xpath('//table/tr/td[6]')]

    def _get_nth_cell_data(self, cell_number, text=False, href=False, link_text=False):
        # Retrieve specific types of data from all nTH cells in the table
        path = '//table/tr/td[%d]' % cell_number
        if text:
            path += '/text()'
        elif href:
            path += '/a/@href'
        elif link_text:
            path += '/a/text()'
        return self.html.xpath(path)
