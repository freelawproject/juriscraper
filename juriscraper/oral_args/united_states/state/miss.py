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


def make_year_iterable(year):
    "returns a (year, sitting) tuple"
    iterable = list()
    for sitting in range(1, 7):
        iterable.append((year, sitting))
    return iterable


def make_back_scrape_iterable():
    iterable = [(2014, 5), (2014, 6)]
    for year in range(2015, 2019):
        iterable += make_year_iterable(year)
    return iterable


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self._url_template = "https://courts.ms.gov/appellatecourts/{court}/archive/{year}/{scourt}{sitting}{year}.php"  # noqa: E501
        self.method = 'GET'
        self.uses_selenium = False
        # Complete this variable if you create a backscraper.
        self.back_scrape_iterable = make_back_scrape_iterable()
        self.url = self._make_url(2018, 6)
        
    def _make_url(self, year, sitting):
        data = dict(year=year, sitting=sitting)
        court_name = dict(court="sc", scourt="scs")
        data.update(court_name)
        return self._url_template.format(**data)

    def _get_download_urls(self):
        path = "//iframe/following-sibling::a"
        return [el.get('href') for el in self.html.xpath(path)]

    def _get_case_names(self):
        case_names = []
        path = "//iframe/following-sibling::a"
        for e in self.html.xpath(path):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(titlecase(s))
        return case_names

    def _get_case_dates(self):
        path = "//iframe"
        elements = self.html.xpath(path)
        date_strings = list()
        for el in elements:
            dtel = el.xpath('./following-sibling::b')
            if not len(dtel):
                dtel = el.xpath('./following-sibling::strong')
            if not len(dtel):
                "Unable to find date {}".format(el)
                raise RuntimeError(msg)
            bel = dtel[0]
            text = bel.text_content()
            dstring = convert_date_string(text)
            date_strings.append(dstring)
        return date_strings

    def _get_docket_numbers(self):
        "This is typically of the form year-casetype-casenumber-court"
        urls = self._get_download_urls()
        return [os.path.basename(u) for u in urls]

    def _download_backwards(self, page_tuple):
        "** this variable is a (year, sitting) tuple **"
        year, sitting = page_tuple
        self.url = self._make_url(year, sitting)
        self.html = self._download()
