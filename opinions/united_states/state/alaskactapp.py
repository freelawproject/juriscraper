"""
Auth: Jon Andersen <janderse@gmail.com>
History:
    2014-08-29 Cloned from alaska.py
"""

from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courtrecords.alaska.gov/webdocs/opinions/ap.htm'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath("//ul[position() > 1 and position() <= 25]/li[descendant::a/em]//em/text()")]

    def _get_download_urls(self):
        return [h for h in self.html.xpath("//ul[position() > 1 and position() <= 25]/li/a[child::em]/@href")]

    def _get_case_dates(self):
        dates = []
        for h2_element in self.html.xpath('//h2[position() <= 24][following-sibling::ul//a/em]'):
            date_string = str(h2_element.xpath('./text()')[0])

            # Older opinions have date headers like: January - March 2014
            if (date_string.find("-") > 0):
                date_string = date_string[date_string.find("-")+1:].strip()

            try:
                date_obj = date.fromtimestamp(
                    time.mktime(time.strptime(date_string, "%B %d, %Y")))
            except ValueError:
                date_obj = date.fromtimestamp(
                    time.mktime(time.strptime(date_string, "%B %Y")))

            # Determine the number of links below the date and add them all to
            # the date list.
            count = len(h2_element.xpath('./following-sibling::ul[1]//a/em'))
            dates.extend([date_obj] * count)
        return dates

    def _get_docket_numbers(self):
        return [t for t in self.html.xpath("//ul[position() > 1 and position() <= 25]/li[descendant::a/em]/text()[1]")]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
