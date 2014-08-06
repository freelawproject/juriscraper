# Author: Michael Lissner
# History:
# - 2013-06-03: Created by mlr.
# - 2014-08-06: Updated for new website by mlr.

from datetime import datetime
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://supreme.nvcourts.gov/Supreme/Decisions/Advance_Opinions/'
        self.xpath_adjustment = 0
        self.selector = 'ctl00_ContentPlaceHolderContent_AdvanceOpinions_GridView1'

    def _get_download_urls(self):
        path = '//table[@id = "{selector}"]//td[{i}]//@href'.format(
            selector=self.selector,
            i=4 + self.xpath_adjustment,
        )
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//table[@id = "{selector}"]//td[{i}]//text()'.format(
            selector=self.selector,
            i=3 + self.xpath_adjustment,
        )
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '//table[@id = "{selector}"]//td[{i}]//text()'.format(
            selector=self.selector,
            i=4 + self.xpath_adjustment,
        )
        return [datetime.strptime(date_string, '%b %d, %Y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//table[@id = "{selector}"]//td[{i}]//text()'.format(
            selector=self.selector,
            i=2 + self.xpath_adjustment,
        )
        return list(self.html.xpath(path))

    def _get_neutral_citations(self):
        neutral_path = '//table[@id = "ctl00_ContentPlaceHolderContent_AdvanceOpinions_GridView1"]//td[1]//text()'
        date_path = '//table[@id = "ctl00_ContentPlaceHolderContent_AdvanceOpinions_GridView1"]//td[4]//text()'
        neutral_citations = []
        for neutral_number, date_string in zip(self.html.xpath(neutral_path), self.html.xpath(date_path)):
            year = datetime.strptime(date_string, '%b %d, %Y').year
            neutral_citations.append('{year} NV {num}'.format(year=year, num=neutral_number))
        return neutral_citations

