#  Scraper for Pennsylvania Commonwealth Court
# CourtID: pacomm
# Court Short Name: pacomm
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014

from juriscraper.opinions.united_states.state import pa
import re


class Site(pa.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.regex = re.compile("(.*)- (\d+.*\d{4})")
        self.url = "http://www.pacourts.us/assets/rss/CommonwealthOpinionsRss.ashx"
