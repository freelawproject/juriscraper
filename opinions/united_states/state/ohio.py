"""Scraper for the Supreme Court of Ohio
CourtID: ohio
Court Short Name: Ohio
Author: Brian Carver
"""

from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        # Changing the page # in the url will get additional pages
        # Changing the source # (0-13) will get the 12 Courts of Appeals and
        # the Court of Claims. We do not use the "all sources" link because a
        # single day might yield more than 25 opinions and this scraper is
        # not designed to walk through multiple pages.
        self.url = ('http://www.sconet.state.oh.us/ROD/docs/default.asp?Page=1&Sort=docdecided%20DESC&PageSize=25&Source=0&iaFilter=2012&ColumnMask=669')
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        # To avoid rows without slip opinions we ensure sibling column has
        # a docket number in it (or more accurately any text != 'foo')
        for txt in self.html.xpath(
        "//table[2]/tr[./td[2]/font[./text() != 'foo']]/td[1]/font/a/text()"):
            case_names.append(txt.replace('(Slip Opinion)', ''))
        return case_names

    def _get_download_urls(self):
        download_urls = []
        # To avoid rows without slip opinions we ensure sibling column has
        # a docket number in it (or more accurately any text != 'foo')
        # Additionally, the site lists each url 2x in this column! We need 1x
        # so a similar technique grabs only the @href's associated with text
        # as the duplicate ones are merely links on an image.
        for txt in self.html.xpath(
        "//table[2]/tr[./td[2]/font[./text() != 'foo']]/td[1]/font/a[./text() != 'foo']/@href"):
            download_urls.append(txt)
        return download_urls

    def _get_docket_numbers(self):
        return [txt for txt in self.html.xpath(
            '//table[2]/tr/td[2]/font/text()')]

    def _get_summaries(self):
        summaries = []
        # To avoid rows without slip opinions we ensure sibling column has
        # a docket number in it (or more accurately any text != 'foo')
        for txt in self.html.xpath(
            "//table[2]/tr[./td[2]/font[./text() != 'foo']]/td[3]/font/text()"):
            summaries.append(txt)
        return summaries

    def _get_case_dates(self):
        dates = []
        # To avoid rows without slip opinions we ensure sibling column has
        # a docket number in it (or more accurately any text != 'foo')
        for txt in self.html.xpath(
            "//table[2]/tr[./td[2]/font[./text() != 'foo']]/td[5]/font/text()"):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                txt.strip(), '%m/%d/%Y'))))
        return dates

    def _get_neutral_citations(self):
        neutral_citations = []
        # To avoid rows without slip opinions we ensure sibling column has
        # a docket number in it (or more accurately any text != 'foo')
        for txt in self.html.xpath(
            "//table[2]/tr[./td[2]/font[./text() != 'foo']]/td[6]/font/text()"):
            neutral_citations.append(txt)
        return neutral_citations

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

"""
# This doesn't work right because even though it pads the list of judges to
# be the same length as the dates, it doesn't insert 'per curiam' in the
# right places. It just pads the end of the list. Perhaps someone can fix.
import itertools

    def _get_judges(self):
        judges = []
        dates = self._get_case_dates()
        # To avoid rows without slip opinions we ensure sibling column has
        # a docket number in it (or more accurately any text != 'foo')
        for txt, dat in itertools.izip_longest(self.html.xpath(
            "//table[2]/tr[./td[2]/font[./text() != 'foo']]/td[4]/font/text()"
            ), dates, fillvalue='per curiam'):
            judges.append(txt)
        return judges
"""
