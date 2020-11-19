# Author: Krist Jin
# 2013-08-18: Created.
# 2014-07-17: Updated by mlr to remedy InsanityException.

from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.opinions.united_states.state import ill


class Site(ill.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "http://www.illinoiscourts.gov/Opinions/recent_appellate.asp"
        )
