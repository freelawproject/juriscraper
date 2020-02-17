"""Scraper for the Mississippi Court of Appeals
CourtID: missctapp
Court Short Name: Miss
Author: umeboshi2
Reviewer: mlr
History:
  2019-01-03: Created by Joseph Rawson
"""
from .miss import Site as MissSite


class Site(MissSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "https://courts.ms.gov/appellatecourts/coa/coaoa.php"

    def _make_url(self, year, sitting):
        data = dict(year=year, sitting=sitting)
        court_name = dict(court="coa", scourt="coa")
        data.update(court_name)
        return self._url_template.format(**data)
