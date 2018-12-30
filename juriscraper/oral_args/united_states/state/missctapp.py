"""Scraper for [Full name of court]
CourtID: [unique abbreviation to be used by software/filesystem]
Court Short Name: [standard abbreviation used in citations]
Author:
Reviewer:
History:
  YYYY-MM-DD: Created by XXX
"""
import os

from lxml import html
from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.string_utils import convert_date_string

from .miss import Site as MissSite


class Site(MissSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "https://courts.ms.gov/appellatecourts/coa/archive/2018/coa{sitting}{year}.php".format(year=2018, sitting=6)  # noqa: E501

    def _download_backwards(self, page_tuple):
        "** this variable is a (year, sitting) tuple **"
        year, sitting = page_tuple
        self.url = "https://courts.ms.gov/appellatecourts/coa/archive/{year}/coa{sitting}{year}.php".format(year=year, sitting=sitting)  # noqa: E501
        self.html = self._download()
