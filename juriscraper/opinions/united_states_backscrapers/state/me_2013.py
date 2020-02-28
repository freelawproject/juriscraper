"""Backscraper for Supreme Court of Maine 2013
CourtID: me
Court Short Name: Me.
Author: Brian W. Carver
Date created: June 20, 2014
"""

from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.opinions.united_states.state import me


class Site(me.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.courts.maine.gov/opinions_orders/supreme/lawcourt/2013/2013_index.shtml"
