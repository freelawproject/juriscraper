"""Scraper for [Full name of court]
CourtID: [unique abbreviation to be used by software/filesystem]
Court Short Name: [standard abbreviation used in citations]
Author:
Reviewer:
History:
  YYYY-MM-DD: Created by XXX
"""
import os
import calendar

from lxml import html
from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.string_utils import convert_date_string

DAYS = [d.lower() for d in calendar.day_name]

def get_first_word(text):
    return text.split()[0]


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


def parse_sibling_text_nodes(iframe):
    textlist = iframe.xpath("./following-sibling::text()")
    textlist = [el.strip() for el in textlist
                if el.strip() and el.strip() != "\\r\\n"]
    if len(textlist) > 1:
        raise RuntimeError("Parsing error on {}".format(textlist))
    return textlist

def parse_emboldened_nodes(iframe):
    # FIXME test './following-sibling::b|strong'
    # or variants
    boldlist = iframe.xpath('./following-sibling::b')
    if not len(boldlist):
        boldlist = iframe.xpath('./following-sibling::strong')
    if not len(boldlist):
        msg = "No emboldened node in {}".format(iframe.getparent())
        raise RuntimeError(msg)
    date_text = None
    while len(boldlist):
        el = boldlist.pop(0)
        text = el.text_content()
        # Expecting date string to start with capitalized day name
        fword = get_first_word(text)
        if fword.endswith(','):
            fword = fword.split(',')[0]
        if fword.lower() not in DAYS:
            continue
        else:
            date_text = text
    return date_text


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self._url_template = "https://courts.ms.gov/appellatecourts/{court}/archive/{year}/{scourt}{sitting}{year}.php"  # noqa: E501
        self.method = 'GET'
        self.uses_selenium = False
        # Complete this variable if you create a backscraper.
        self.back_scrape_iterable = make_back_scrape_iterable()
        self.url = "https://courts.ms.gov/appellatecourts/sc/scoa.php"

    def _make_url(self, year, sitting):
        data = dict(year=year, sitting=sitting)
        court_name = dict(court="sc", scourt="scs")
        data.update(court_name)
        return self._url_template.format(**data)

    def _get_download_urls(self):
        path = "//iframe/following-sibling::a"
        urls = list()
        for el in self.html.xpath(path):
            href = el.get('href')
            if href not in urls:
                urls.append(href)
        return urls

    def _get_case_names(self):
        case_names = list()
        path = "//iframe/following-sibling::a"
        urls = list()
        for el in self.html.xpath(path):
            href = el.get('href')
            if href not in urls:
                urls.append(href)
                s = html.tostring(el, method='text', encoding='unicode')
                case_names.append(titlecase(s))
        return case_names

    def _get_case_dates(self):
        path = "//iframe"
        elements = self.html.xpath(path)
        dates = list()
        for el in elements:
            tlist = parse_sibling_text_nodes(el)
            if len(tlist):
                text = tlist[0]
            else:
                text = parse_emboldened_nodes(el)
            date = convert_date_string(text)
            dates.append(date)
        return dates

    def _get_docket_numbers(self):
        "This is typically of the form year-casetype-casenumber-court"
        urls = self._get_download_urls()
        return [os.path.basename(u) for u in urls]

    def _download_backwards(self, page_tuple):
        "** this variable is a (year, sitting) tuple **"
        year, sitting = page_tuple
        self.url = self._make_url(year, sitting)
        self.html = self._download()
