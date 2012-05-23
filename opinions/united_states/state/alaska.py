from juriscraper.GenericSite import GenericSite
import time
from datetime import date


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courts.alaska.gov/sp.htm'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath("//ul/li[descendant::a/em]//em/text()")]

    def _get_download_urls(self):
        return [h for h in self.html.xpath("//ul[position() > 1]/li/a[child::em]/@href")]

    def _get_case_dates(self):
        dates = []
        for h2_element in self.html.xpath('//h2[following-sibling::ul//a/em]'):
            date_string = str(h2_element.xpath('./text()')[0])
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
        return [t for t in self.html.xpath("//ul[position() > 1]/li[descendant::a/em]/text()[1]")]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
