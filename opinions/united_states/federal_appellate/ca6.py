import time
from datetime import date, timedelta

from juriscraper.OpinionSite import OpinionSite
from dateutil.rrule import rrule, DAILY


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.ca6.uscourts.gov/cgi-bin/opinions.pl'
        self.method = 'POST'
        self.parameters = {
            'CASENUM': '',
            'TITLE': '',
            'FROMDATE': date.strftime(date.today(), '%m/%d/%Y'),
            'TODATE': date.strftime(date.today(), '%m/%d/%Y'),
            'OPINNUM': ''
        }
        self.court_id = self.__module__
        self.interval = 30
        self.back_scrape_iterable = [i.date() for i in rrule(
            DAILY,
            interval=self.interval,  # Every interval days
            dtstart=date(2000, 1, 1),
            until=date(2016, 1, 1),
        )]

    def _get_case_names(self):
        return [e for e in self.html.xpath('//table/tr/td[4]/text()[1]')]

    def _get_download_urls(self):
        return [e for e in self.html.xpath('//table/tr/td[1]/a/@href')]

    def _get_case_dates(self):
        dates = []
        for text_string in self.html.xpath('//table/tr/td[3]/text()'):
            date_string = text_string.strip()
            dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%Y/%m/%d'))))
        return dates

    def _get_docket_numbers(self):
        return [num.strip() for num in self.html.xpath('//table/tr/td[2]/a/text()')]

    def _get_precedential_statuses(self):
        statuses = []
        for filename in self.html.xpath('//table/tr/td[1]/a/text()'):
            if 'n' in filename.lower():
                statuses.append('Unpublished')
            elif 'p' in filename.lower():
                statuses.append('Published')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_lower_courts(self):
        lower_courts = []
        for e in self.html.xpath('//tr[position() > 1]/td[4]/font'):
            try:
                lower_courts.append(e.xpath('./text()')[0].strip())
            except IndexError:
                lower_courts.append('')
        return lower_courts

    def _download_backwards(self, d):
        self.parameters = {
            'CASENUM': '',
            'TITLE': '',
            'FROMDATE': d.strftime('%m/%d/%Y'),
            'TODATE': (d + timedelta(self.interval)).strftime('%m/%d/%Y'),
            'OPINNUM': ''
        }

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def _post_parse(self):
        """This will remove the cases without a case name"""
        to_be_removed = [index for index, case_name in
                         enumerate(self.case_names)
                         if not case_name.replace('v.', '').strip()]

        for attr in self._all_attrs:
            item = getattr(self, attr)
            if item is not None:
                new_item = self.remove_elements(item, to_be_removed)
                self.__setattr__(attr, new_item)

    @staticmethod
    def remove_elements(list_, indexes_to_be_removed):
        return [i for j, i in enumerate(list_) if j not in indexes_to_be_removed]
