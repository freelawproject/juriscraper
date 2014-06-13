"""Scraper for the United States Court of Appeals for Veterans Claims
CourtID: cavc
Court Short Name: Vet.App.
"""

from juriscraper.OpinionSite import OpinionSite
import time
import datetime
from datetime import date
from lxml import html


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = ('http://www.uscourts.cavc.gov/opinions.php')
        self.court_id = self.__module__

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//div/ul/li/ul/li/table/tr/td/a'):
            s = ', '.join([t.strip() for t in e.xpath('text()') if t.strip()])
            docket_numbers.append(s)
        return docket_numbers

    def _get_download_urls(self):
        return [txt for txt in self.html.xpath('//div/ul/li/ul/li/table/tr/td/a/@href')]

    def _get_case_dates(self):
        dates = []
        for txt in self.html.xpath('//div/ul/li/ul/li/table/tr/td[3]/text()'):
            if txt == '20JUN008':
                dates.append(date.fromtimestamp(time.mktime(time.strptime('20JUN08', '%d%b%y'))))
            else:
                dates.append(date.fromtimestamp(time.mktime(time.strptime(txt, '%d%b%y'))))
        return dates

    # http://en.wikipedia.org/wiki/United_States_Secretary_of_Veterans_Affairs
    # provided the names to append here for different opinion dates.
    # Covering all possibilities here.
    def _get_case_names(self):
        case_names = []
        dates = self._get_case_dates()
        appellants = []
        for e in self.html.xpath('//div/ul/li/ul/li/table/tr/td[1]'):
            app = ', '.join([t.strip() for t in e.xpath('text()') if t.strip()])
            appellants.append(app)
        for txt, dat in zip(appellants, dates):
            if dat > datetime.date(2009, 1, 20):
                case_names.append(txt + ' v. Shinseki')
            elif dat > datetime.date(2007, 12, 20):
                case_names.append(txt + ' v. Peake')
            elif dat > datetime.date(2007, 10, 1):
                case_names.append(txt + ' v. Mansfield')
            elif dat > datetime.date(2005, 1, 26):
                case_names.append(txt + ' v. Nicholson')
            elif dat > datetime.date(2001, 1, 23):
                case_names.append(txt + ' v. Principi')
            elif dat > datetime.date(2000, 7, 25):
                case_names.append(txt + ' v. Gober')
            elif dat > datetime.date(1998, 1, 2):
                case_names.append(txt + ' v. West')
            elif dat > datetime.date(1997, 7, 1):
                case_names.append(txt + ' v. Gober')
            elif dat > datetime.date(1993, 1, 22):
                case_names.append(txt + ' v. Brown')
            elif dat > datetime.date(1992, 9, 26):
                case_names.append(txt + ' v. Principi')
            else:
                case_names.append(txt + ' v. Derwinski')
        return case_names

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)
