"""Scraper for the Supreme Court of Ohio
CourtID: ohio
Court Short Name: Ohio
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
        self.court_index = 0
        self.url = ('http://www.sconet.state.oh.us/ROD/docs/default.asp?Page=1&Sort=docdecided%20DESC&PageSize=100&Source={court}&iaFilter={year}&ColumnMask=669'.format(
            court=self.court_index,
            year=date.today().year)
        )
        self.court_id = self.__module__
        self.base_path = "id('Table1')//tr[position() > 1]/td[2][contains(., '-')]"

    def _get_case_names(self):
        path = "{base}/preceding::td[1]//text()".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_download_urls(self):
        path = "{base}/preceding::td[1]//a[1]/@href".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_docket_numbers(self):
        path = "{base}//text()".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_summaries(self):
        path = "{base}/following::td[1]//text()".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "{base}/following::td[3]//text()".format(base=self.base_path)
        dates = []
        for txt in self.html.xpath(path):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(
                txt.strip(), '%m/%d/%Y'))))
        return dates

    def _get_neutral_citations(self):
        path = "{base}/following::td[4]//text()".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_judges(self):
        path = "{base}/following::td[2]".format(base=self.base_path)
        return map(self._return_judge, self.html.xpath(path))

    @staticmethod
    def _return_judge(e):
        txt = e.xpath(".//text()")
        if txt:
            return txt[0]
        else:
            return 'per curiam'