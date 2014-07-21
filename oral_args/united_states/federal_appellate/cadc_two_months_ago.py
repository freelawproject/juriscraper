"""Scraper for D.C. Circuit of Appeals
CourtID: cadc
Court Short Name: cadc
Author: mlr
Reviewer: None
Date created: 18 July 2014
"""

from datetime import date

import cadc


class Site(cadc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        d = date.today()
        month = int(d.strftime('%m')) - 2
        year = d.strftime('%Y')
        self.url = 'http://www.cadc.uscourts.gov/recordings/recordings.nsf/DocsByRDate?OpenView&count=100&SKey={year}{month:02}'.format(
            year=year,
            month=month,
        )
