""" Scraper for Pennsylvania Commonwealth Court
CourtID: pacomm
Court Short Name: pacomm
Author: Andrei Chelaru
Reviewer: mlr
Date created: 21 July 2014

If there are errors with this site, you can contact:

  Amanda Emerson
  717-255-1601

She's super responsive.
"""

from juriscraper.opinions.united_states.state import pa
import re


class Site(pa.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.regex = re.compile("(.*)- (\d+.*\d{4})")
        self.url = "http://www.pacourts.us/assets/rss/CommonwealthOpinionsRss.ashx"
        self.base = "//item[not(contains(title/text(), 'Judgment List'))]" \
                          "[not(contains(title/text(), 'Reargument Table'))]"
