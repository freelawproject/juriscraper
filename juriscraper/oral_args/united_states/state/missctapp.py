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
        self.url = "https://courts.ms.gov/appellatecourts/coa/coaoa.php"

    def _make_url(self, year, sitting):
        data = dict(year=year, sitting=sitting)
        court_name = dict(court="coa", scourt="coa")
        data.update(court_name)
        return self._url_template.format(**data)
