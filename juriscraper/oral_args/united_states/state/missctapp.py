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

    def _get_case_dates(self):
        """ This is an example of a date field. Note that the format string
            will likely need to be updated to  match the date formats
            on the site you are scraping. The datetime formats can be found
            here: http://docs.python.org/2/library/datetime.html
        """
        path = "//table/tr/td/iframe/following-sibling::a"
        # path = '//path/to/text/text()'
        elements = self.html.xpath(path)
        date_strings = list()
        #el = elements[0]
        #import pdb ; pdb.set_trace()
        for el in elements:
            bel = el.getnext()
            text = bel.text_content()
            import pdb ; pdb.set_trace()
            dstring = convert_date_string(text)
            date_strings.append(dstring)
        return date_strings
    
    def _download_backwards(self, page_tuple):
        """ This is a simple method that can be used to generate Site objects
            that can be used to paginate through a court's entire website.

            This method is usually called by a backscraper caller (see the
            one in CourtListener/alert/scrapers for details), and typically
            modifies aspects of the Site object's attributes such as Site.url.

            A simple example has been provided below. The idea is that the
            caller runs this method with a different variable on each
            iteration.
            That variable is often a date that is getting iterated or is simply
            a index (i), that we iterate upon.
            ** this variable is a (year, sitting) tuple **
        """
        year, sitting = page_tuple
        self.url = "https://courts.ms.gov/appellatecourts/coa/archive/2018/coa{sitting}{year}.php".format(year=year, sitting=sitting)  # noqa: E501
        self.html = self._download()
