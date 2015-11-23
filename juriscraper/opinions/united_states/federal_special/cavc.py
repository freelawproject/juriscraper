"""Scraper for the United States Court of Appeals for Veterans Claims
CourtID: cavc
Court Short Name: Vet.App.
History:
 - 2012-06-07: Created by Brian Carver
 - 2014-08-06: Updated by mlr.
"""

from juriscraper.OpinionSite import OpinionSite
import time
import datetime
from datetime import date


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.uscourts.cavc.gov/opinions.php'
        self.court_id = self.__module__

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath("//*[@id='oasteps_boxes']//td[2]/a"):
            s = ', '.join([t.strip() for t in e.xpath('text()') if t.strip()])
            docket_numbers.append(s)
        return docket_numbers

    def _get_download_urls(self):
        return list(self.html.xpath("//*[@id='oasteps_boxes']//td[2]//@href"))

    def _get_case_dates(self):
        dates = []
        for txt in self.html.xpath("//*[@id='oasteps_boxes']//td[3]//text()"):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(txt, '%d%b%y'))))
        return dates

    def _get_case_names(self):
        case_names = []
        dates = self._get_case_dates()
        appellants = []
        for e in self.html.xpath("//*[@id='oasteps_boxes']//td[1]"):
            app = ', '.join([t.strip() for t in e.xpath('text()') if t.strip()])
            appellants.append(app)
        for t, d in zip(appellants, dates):
            # See: http://en.wikipedia.org/wiki/United_States_Secretary_of_Veterans_Affairs
            if d > datetime.date(2014, 7, 30):
                case_names.append(t + 'v. McDonald')
            elif d > datetime.date(2014, 5, 30):
                case_names.append(t + ' v. Gibson')
            elif d > datetime.date(2009, 1, 20):
                case_names.append(t + ' v. Shinseki')
            elif d > datetime.date(2007, 12, 20):
                case_names.append(t + ' v. Peake')
            elif d > datetime.date(2007, 10, 1):
                case_names.append(t + ' v. Mansfield')
            elif d > datetime.date(2005, 1, 26):
                case_names.append(t + ' v. Nicholson')
            elif d > datetime.date(2001, 1, 23):
                case_names.append(t + ' v. Principi')
            elif d > datetime.date(2000, 7, 25):
                case_names.append(t + ' v. Gober')
            elif d > datetime.date(1998, 1, 2):
                case_names.append(t + ' v. West')
            elif d > datetime.date(1997, 7, 1):
                case_names.append(t + ' v. Gober')
            elif d > datetime.date(1993, 1, 22):
                case_names.append(t + ' v. Brown')
            elif d > datetime.date(1992, 9, 26):
                case_names.append(t + ' v. Principi')
            else:
                case_names.append(t + ' v. Derwinski')
        return case_names

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)
