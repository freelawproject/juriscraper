# History:
#   2015-10-20: Created by Andrei Chelaru

from typing_extensions import Unpack

from juriscraper.AbstractSite import SiteOptions
from juriscraper.opinions.united_states_backscrapers.state import ill


class Site(ill.Site):
    def __init__(self, **kwargs: Unpack[SiteOptions[int]]) -> None:
        super().__init__(**kwargs)
        self.court_id = self.__module__
        self.url_base = "http://www.illinoiscourts.gov/Opinions/AppellateCourt/{year}/2ndDistrict/default.asp"
