"""Scraper for the United States Court of Appeals for the Armed Forces
CourtID: armfor
Court Short Name: C.A.A.F."""

from datetime import date, datetime

from juriscraper.OpinionSite import OpinionSite
from lxml import html


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        today = date.today()
        if today.month > 8 and today.day > 4:
            url_year = today.year
        else:
            url_year = today.year - 1
        self.url = 'http://www.armfor.uscourts.gov/newcaaf/opinions/%sSepTerm.htm' % url_year
        self.court_id = self.__module__

    def _get_case_names(self):
        return [t for t in self.html.xpath('//table//tr[descendant::a]/td[1]/font/text()')]

    def _get_download_urls(self):
        return [t for t in self.html.xpath('//table//tr[descendant::a]/td[2]/font/a/@href')]

    def _get_case_dates(self):
        dates = []
        date_formats = ('%b %d, %Y', '%B %d, %Y')
        for s in self.html.xpath('//table//tr[descendant::a]/td[3]/font/text()'):
            s = s.strip()
            for date_format in date_formats:
                try:
                    dates.append(datetime.strptime(s, date_format).date())
                    break
                except ValueError:
                    continue
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//table//table//tr[descendant::a and position() > 1]/td[2]'):
            s = html.tostring(e, method='text', encoding='unicode')
            docket_numbers.append(s.strip()[:-5])
        return docket_numbers

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)
