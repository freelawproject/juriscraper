from juriscraper.GenericSite import GenericSite
from datetime import date
from datetime import datetime
from datetime import timedetla


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://pacer.ca4.uscourts.gov/cgi-bin/opinions.pl'
        self.court_id = self.__module__
        td = date.today()
        self.parameters = {'CASENUM': '',
                           'FROMDATE': (td - timedetla(days=20)).strftime('%m-%d-%Y'),
                           'TITLE': '',
                           'TODATE': td.strftime('%m-%d-%Y')}
        self.method = 'POST'

    def _get_case_names(self):
        path = '//td[4]/text()'
        return list(self.html.xpath(path))

    def _get_download_urls(self):
        path = '//td[1]/a/@href'
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '//td[3]/text()'
        return [datetime.strptime(date_string, '%Y/%m/%d').date()
                for date_string in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = '//td[2]//text()'
        return list(self.html.xpath(path))

    def _get_precedential_statuses(self):
        statuses = []
        # using download link, we can get the statuses
        for download_url in self.download_urls:
            file_name = download_url.split('/')[-1]
            if 'u' in file_name.lower():
                statuses.append('Unpublished')
            else:
                statuses.append('Published')
        return statuses

    def _download_backwards(self, dt):
        self.parameters['FROMDATE'] = dt.strftime('%m-%d-%Y')
        self.parameters['TODATE'] = (dt - timedetla(days=9)).strftime('%m-%d-%Y')
        self.html = self._download()
