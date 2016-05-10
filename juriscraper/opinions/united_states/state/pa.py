#  Scraper for Pennsylvania Supreme Court
# CourtID: pa
# Court Short Name: pa
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 21 July 2014


from datetime import datetime
import re

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.regex = re.compile("(.*)(?:[,-]?\s+Nos?\.)(.*)", re.MULTILINE)
        self.url = 'http://www.pacourts.us/assets/rss/SupremeOpinionsRss.ashx'
        self.base = "//item[not(contains(title/text(), 'Judgment List'))]" \
                          "[not(contains(title/text(), 'Reargument Table'))]" \
                          "[contains(title/text(), 'No.')]"

    def _get_case_names(self):
        path = "{base}/title/text()".format(base=self.base)
        return map(self._return_case_name, self.html.xpath(path))

    def _return_case_name(self, s):
        match = self.regex.search(s)
        return match.group(1)

    def _get_download_urls(self):
        path = "{base}//@href".format(base=self.base)
        return [item for item in self.html.xpath(path)]

    def _get_case_dates(self):
        path = "{base}/pubdate/text()".format(base=self.base)
        # Isolate '29Jul2014' from a string like 'Tue, 29 Jul 2014 04:00:00 GMT'
        return [datetime.strptime(''.join(s.split(' ')[1:4]), '%d%b%Y').date()
                for s in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "{base}/title/text()".format(base=self.base)
        return map(self._return_docket_number, self.html.xpath(path))

    def _return_docket_number(self, e):
        match = self.regex.search(e)
        return match.group(2)

    def _get_judges(self):
        path = "{base}/creator/text()".format(base=self.base)
        return list(self.html.xpath(path))
