"""Scraper for the Supreme Court of Vermont
CourtID: vt
Court Short Name: VT
Author: Brian W. Carver
Date created: 18 Aug 2013
Reviewer: Mike Lissner

If there are errors with the site, you can contact:

 Monica Bombard
 (802) 828-4784

She's very responsive.
"""

from datetime import datetime

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'https://www.vermontjudiciary.org/LC/SupCrtPublish.aspx'

    def _get_download_urls(self):
        path = "//div[@id='WebPartWPQ2']//a[contains(@href, 'pdf')]/@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "//div[@id='WebPartWPQ2']//td[2]//text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "//div[@id='WebPartWPQ2']//td[5]//text()"
        return [datetime.strptime(s, '%m/%d/%Y') for s in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "//div[@id='WebPartWPQ2']//td[4]//text()"
        return list(self.html.xpath(path))

    def _get_neutral_citations(self):
        path = "//div[@id='WebPartWPQ2']//td[3]//text()"
        return list(self.html.xpath(path))
