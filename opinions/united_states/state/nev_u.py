# Author: Michael Lissner
# History:
#  - 2013-06-03: Created by mlr.
#  - 2014-08-06: Updated by mlr for new website.

from juriscraper.lib.string_utils import titlecase
from juriscraper.opinions.united_states.state import nev_p


class Site(nev_p.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://supreme.nvcourts.gov/Supreme/Decisions/Unpublished_Orders/'
        self.xpath_adjustment = -1
        self.selector = 'ctl00_ContentPlaceHolderContent_UnpublishedOrders_GridView1'

    def _get_case_names(self):
        # Runs the code from super, but titlecases.
        names = super(Site, self)._get_case_names()
        return [titlecase(name.lower()) for name in names]

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)

    def _get_neutral_citations(self):
        # None for unpublished.
        return None
