"""Scraper for U.S. Merit Systems Protection Board
CourtID: mspb
Court Short Name: MSPB
Author: Jon Andersen
Reviewer:
Date created: 1 Sep 2014
Type: Precedential
"""

import re
import random
from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.mspb.gov/netsearch/decisiondisplay_2011.aspx?timelapse=3&displaytype=2368396&description=Precedential%20Decisions&cachename=a' + str(random.randrange(1, 100000000))
        # Complete this variable if you create a backscraper.
        self.back_scrape_iterable = None

    def _get_download_urls(self):
        """
            Like: http://www.mspb.gov/netsearch/viewdocs.aspx?docnumber=1075720&version=1080035&application=ACROBAT
        """
        path = "//tr[@class='ITEMS']/td[3]/a/@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        """
            Like: {Appellant} v. {Agency}
        """
        path = "//tr[@class='ITEMS']/td[3]/a/text()"
        appellants = self.html.xpath(path)

        path = "//tr[@class='ITEMS']/td[4]/text()"
        agencies = self.html.xpath(path)

        return ["%s v. %s" % (appellant, agency) for (appellant, agency) in zip(appellants, agencies)]

    def _get_case_dates(self):
        """
            Like: Aug 06, 2014
        """
        path = "//tr[@class='ITEMS']/td[1]/span/text()"
        return [datetime.strptime(date_string, '%b %d, %Y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        statuses.extend(["Published"] * len(self.case_dates))
        return statuses

    def _get_neutral_citations(self):
        """
          Like: 2014 MSPB 68
        """
        path = "//tr[@class='ITEMS']/td[2]/text()"
        return [s.replace('\u00A0', ' ') for s in self.html.xpath(path)]
