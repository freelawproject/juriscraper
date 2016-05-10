# History:
#   2015-10-20: Created by Andrei Chelaru

from ill import Site as IllSite


class Site(IllSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url_base = 'http://www.illinoiscourts.gov/Opinions/AppellateCourt/{year}/3rdDistrict/default.asp'
