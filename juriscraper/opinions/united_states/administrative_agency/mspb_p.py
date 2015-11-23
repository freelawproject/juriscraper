"""Scraper for U.S. Merit Systems Protection Board
CourtID: mspb
Court Short Name: MSPB
Author: Jon Andersen
Reviewer: mlr
Date created: 1 Sep 2014
Type: Precedential
"""

import random
from datetime import datetime

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.mspb.gov/netsearch/decisiondisplay_2011.aspx?timelapse=3&displaytype=2368396&description=Precedential%20Decisions&cachename=a' + str(random.randrange(1, 100000000))
        self.column_diff = 0

    def _get_download_urls(self):
        """
            Like: http://www.mspb.gov/netsearch/viewdocs.aspx?docnumber=1075720&version=1080035&application=ACROBAT
        """
        path = "//tr[@class='ITEMS']/td[%s]/a/@href" % (3 + self.column_diff)
        return list(self.html.xpath(path))

    def _get_case_names(self):
        """
            Like: {Appellant} v. {Agency}
        """
        path = "//tr[@class='ITEMS']/td[%s]/a/text()" % (3 + self.column_diff)
        appellants = self.html.xpath(path)
        path = "//tr[@class='ITEMS']/td[%s]/text()" % (4 + self.column_diff)
        agencies = self.html.xpath(path)
        return ["%s v. %s" % (appellant, agency)
                for (appellant, agency)
                in zip(appellants, agencies)]

    def _get_case_dates(self):
        """
            Like: Aug 06, 2014
        """
        path = "//tr[@class='ITEMS']/td[1]/span/text()"
        return [datetime.strptime(date_string, '%b %d, %Y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)

    def _get_neutral_citations(self):
        """
          Like: 2014 MSPB 68
        """
        path = "//tr[@class='ITEMS']/td[2]/text()"
        return [s.replace('\u00A0', ' ') for s in self.html.xpath(path)]

    def _get_case_name_shorts(self):
        # We don't (yet) support short case names for administrative bodies.
        return None
