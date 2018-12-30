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


appellate_url = "https://courts.ms.gov/appellatecourts"


def get_sitting_basename(year, sitting, court='coa'):
    if court == 'sc':
        court = 'scs'
    return "{}{}{}.php".format(court, sitting, year)


def get_sitting_url(year, sitting, court='coa'):
    basename = get_sitting_basename(year, sitting, court)
    return os.path.join(appellate_url, court, 'archive', str(year), basename)


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
        self.url = "https://courts.ms.gov/appellatecourts/sc/archive/2018/scs{sitting}{year}.php".format(year=2018, sitting=6)  # noqa: E501
        self.method = 'GET'
        self.uses_selenium = False
        # Complete this variable if you create a backscraper.
        self.back_scrape_iterable = make_back_scrape_iterable()

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
        self.url = "https://courts.ms.gov/appellatecourts/sc/archive/{year}/scs{sitting}{year}.php".format(year=year, sitting=sitting)  # noqa: E501
        self.html = self._download()
