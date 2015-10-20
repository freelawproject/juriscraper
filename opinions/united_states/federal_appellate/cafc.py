from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.cafc.uscourts.gov/opinions-orders?field_origin_value=All&field_report_type_value=All'
        self.back_scrape_iterable = range(1, 700)
        self.court_id = self.__module__

    def _get_case_names(self):
        return [titlecase(s.split('[')[0]) for s in
                self.html.xpath('//table//tr/td[4]/a/text()')]

    def _get_download_urls(self):
        return list(self.html.xpath('//table//tr/td[4]/a/@href'))

    def _get_case_dates(self):
        path = '//table//tr/td[1]/span/text()'
        return [datetime.strptime(date_string, '%Y-%m-%d').date()
                for date_string in self.html.xpath(path)]

    def _get_docket_numbers(self):
        return list(self.html.xpath('//table//tr/td[2]/text()'))

    def _get_precedential_statuses(self):
        statuses = []
        for status in self.html.xpath('//table//tr/td[5]/text()'):
            if 'nonprecedential' in status.lower():
                statuses.append('Unpublished')
            elif 'precedential' in status.lower():
                statuses.append('Published')
            else:
                statuses.append('Unknown')
        return statuses

    def _download_backwards(self, n):
        self.url = "http://www.cafc.uscourts.gov/opinions-orders?page={}".format(n)

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
