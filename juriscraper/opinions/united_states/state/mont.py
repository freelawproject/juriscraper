# Author: Michael Lissner
# Date created: 2013-06-03

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.lib.html_utils import get_table_column_text, get_table_column_links


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'https://courts.mt.gov/Portals/189/orders/orders/Recent_Orders.htm'
        # Site has non-chained, bad certificate, need to
        # ignore ssl verification for now for scraper to work
        self.request['verify'] = False

    def _get_download_urls(self):
        return get_table_column_links(self.html, 1)

    def _get_case_names(self):
        return get_table_column_text(self.html, 4)

    def _get_case_dates(self):
        return [convert_date_string(date_string) for date_string in get_table_column_text(self.html, 2)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        return get_table_column_text(self.html, 3)

    def _get_summaries(self):
        return get_table_column_text(self.html, 1)

    def _get_nature_of_suit(self):
        natures = []
        for docket in self.docket_numbers:
            if docket.startswith('DA'):
                nature = 'Direct Appeal'
            elif docket.startswith('OP'):
                nature = 'Original Proceeding'
            elif docket.startswith('PR'):
                nature = 'Professional Regulation'
            elif docket.startswith('AF'):
                nature = 'Administrative File'
            else:
                nature = 'Unknown'
            natures.append(nature)
        return natures
