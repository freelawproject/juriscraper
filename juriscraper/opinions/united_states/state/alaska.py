"""
Auth: Jordan Atanasov <jordan.atanasov@commetric.com>
History:
    2012-05-07: Written by Jordan.
    2012-07-06: Updated by mlr to only get the first ten items.
    2015-07-28: Updated by m4h7 to have improved xpaths.
Notes: Only queries first ten dates. Beyond that, they get messy.
"""

import time
from datetime import date

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courtrecords.alaska.gov/webdocs/opinions/sp.htm'
        self.court_id = self.__module__
        # Test whether the selected node does NOT have the class
        self.h4_test = "[not(@class = 'h4interiorpagecontentsubtitle')]"
        # Test for the first h4 prior to the selected node, and make sure it
        # does not have the class described in self.h4_test. This ensures that
        # dates like "April - June 2015" don't get selected.
        self.node_test = "[preceding-sibling::h4[1]%s]" % self.h4_test

    def _get_case_names(self):
        return [e for e in self.html.xpath("//ul%s/li[descendant::a/em]//em/text()" % self.node_test)]

    def _get_download_urls(self):
        return [h for h in self.html.xpath("//ul%s/li/a[child::em]/@href" % self.node_test)]

    def _get_case_dates(self):
        dates = []
        for h4_element in self.html.xpath('//h4%s' % self.h4_test):
            date_string = str(h4_element.xpath('./text()')[0])
            try:
                date_obj = date.fromtimestamp(
                      time.mktime(time.strptime(date_string, "%B %d, %Y")))
            except ValueError:
                date_obj = date.fromtimestamp(
                      time.mktime(time.strptime(date_string, "%B %Y")))

            # Determine the number of links below the date and add them all to
            # the date list.
            count = len(h4_element.xpath('./following-sibling::ul[1]//a/em'))
            dates.extend([date_obj] * count)
        return dates

    def _get_docket_numbers(self):
        return [t for t in self.html.xpath("//ul%s/li[descendant::a/em]/text()[1]" % self.node_test)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
