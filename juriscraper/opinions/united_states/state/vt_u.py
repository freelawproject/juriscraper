"""Scraper for the Supreme Court of Vermont
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vermontjudiciary.org/website-feedback-form
Author: Brian W. Carver
Date created: 18 Aug 2013
Reviewer: Mike Lissner
"""

from datetime import datetime
from six.moves.urllib.parse import urlsplit

from juriscraper.OpinionSite import OpinionSite
from lxml import html


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'https://www.vermontjudiciary.org/lc/masterpages/unpublishedeo2011-present.aspx'

    def _get_download_urls(self):
        path = "//div[@id='WebPartWPQ2']//td[../td[2]/text()]/a[contains(@href, 'pdf')]/@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = "//div[@id='WebPartWPQ2']//td[1][../td[2]/text()]//text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "//div[@id='WebPartWPQ2']//td[2]//text()"
        return [datetime.strptime(s, '%m/%d/%Y') for s in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "//div[@id='WebPartWPQ2']//td[../td[2]/text()]/a[contains(@href, 'pdf')]/@href"
        docket_numbers = []
        for s in self.html.xpath(path):
            # Get the docket number from the URL.
            parts = urlsplit(s)
            # https://www.vt.org/LC/blah/eo15-092.pdf --> '2015-092'
            docket_numbers.append(
                parts.path.split('/')[-1].split('.')[0].replace('eo', '20')
            )
        return docket_numbers

    def _get_dispositions(self):
        path = "//div[@id='WebPartWPQ2']//td[5][../td[2]/text()]//text()"
        return list(self.html.xpath(path))

    def _get_lower_court_judges(self):
        path = "//div[@id='WebPartWPQ2']//td[4][../td[2]/text()]"
        lc_judges = []
        for e in self.html.xpath(path):
            lc_judges.append(html.tostring(e, method='text', encoding='unicode'))
        return lc_judges
