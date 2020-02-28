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
        self.column_diff = 0
        # Something fishy is going on with this court's site. They
        # seem to be blocking/hiding results based on our regular
        # 'juriscraper' User-Agent header. We contacted the
        # court multiple times to work work with them on exploring
        # and resolving this issue, but they were virtually worthless
        # in that email exchange. Since they have been unhelpful, cannot
        # provide more information, and don't seem to care, we will
        # utilize this workaround and sacrifice the courtesy of
        # identifying ourselves with the 'juriscraper' UA. The below
        # workaround is required to shows results for this scraper,
        # and also to show results (and prevent timeout) for mspb_u child.
        self.request["headers"] = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
        }
        self.type = "Precedential"
        self.display = 2368396
        self.set_url()

    def set_url(self):
        cache_key = "a" + str(random.randrange(1, 100000000))
        pattern = (
            "https://www.mspb.gov/MSPBSEARCH/decisiondisplay_2011.aspx?timelapse=12&displaytype=%d&description=%s+Decisions&cachename="
            + cache_key
        )
        self.url = pattern % (self.display, self.type)

    def _get_download_urls(self):
        """Example: http://www.mspb.gov/netsearch/viewdocs.aspx?docnumber=1075720&version=1080035&application=ACROBAT"""
        path = "//tr[@class='ITEMS']/td[%s]/a/@href" % (3 + self.column_diff)
        return list(self.html.xpath(path))

    def _get_case_names(self):
        """Example: {Appellant} v. {Agency}"""
        path = "//tr[@class='ITEMS']/td[%s]/a/text()" % (3 + self.column_diff)
        appellants = self.html.xpath(path)
        path = "//tr[@class='ITEMS']/td[%s]/text()" % (4 + self.column_diff)
        agencies = self.html.xpath(path)
        return [
            "%s v. %s" % (appellant, agency)
            for (appellant, agency) in zip(appellants, agencies)
        ]

    def _get_case_dates(self):
        """Example: Aug 06, 2014"""
        path = "//tr[@class='ITEMS']/td[1]/span/text()"
        return [
            datetime.strptime(date_string, "%b %d, %Y").date()
            for date_string in self.html.xpath(path)
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)

    def _get_neutral_citations(self):
        """Example: 2014 MSPB 68"""
        path = "//tr[@class='ITEMS']/td[2]/text()"
        return [s.replace("\u00A0", " ") for s in self.html.xpath(path)]

    def _get_case_name_shorts(self):
        # We don't (yet) support short case names for administrative bodies.
        return None
